" ============================================================================
" File:        aicatpy.vim
" Description: ai-cat.py integration
" Author:      Attila M. Magyar
" License:     BSD 3-clause
" Website:     https://github.com/attilammagyar/ai-cat
" Version:     1.0.0
"
" Usage:
" - Make sure that your PATH variable is set up correctly so that ai-cat.py can
"   be run.
" - The :AI command initializes a new conversation in the current buffer, or
"   if it is already initialized, it runs the conversation through ai-cat.py.
" - The <TAB> key will run the selected code through ai-cat.py with the last
"   used ai-cat.py settings and replace the selection with the results. Example
"   use case: add to-do comments and instructions to a function declaration,
"   then let the AI implement it. If the AI fails to produce a suitable
"   replacement or there are conflicting modifications in the buffer while the
"   AI is working, then the results are opened in a new tab so you can decide
"   how to proceed with them.
" ============================================================================

if exists("g:loaded_aicatpy")
    finish
endif
let g:loaded_aicatpy = 1


" Trickery to simulate asynchronous command execution in single-threaded Vim
" using background shell execution and cursor events as result checker timer
" triggers.
" Note: A background task belongs to the buffer where it was initiated, so to
" see its results, you need to switch back to that tab/window/buffer.
let g:system_async_tasks = []
let g:system_async_orig_updatetime = &updatetime
let g:system_async_timer_set_up = 0
let g:system_async_num_running_tasks = 0

function! CallFuncByName(name, arg1, arg2, arg3, arg4)
    echo "CallFuncByName: " . a:name

    let l:Func = function(a:name)

    call Func(a:arg1, a:arg2, a:arg3, a:arg4)
endfunction

function! SystemAsync(command, stdin, ok_callback, err_callback, data)
    let l:current_file = expand("%")

    if has("win32")
        echohl None | echo "Running " . a:command . "..."

        " Windows shell is crap, fallback to synchronous execution.
        let l:output = system(a:command, a:stdin)
        let l:output = split(l:output, "\n", 1)

        if v:shell_error == 0
            call CallFuncByName(a:ok_callback, l:current_file, l:output, [""], a:data)
        else
            call CallFuncByName(a:err_callback, l:current_file, l:output, [""], a:data)
        endif

        return
    endif

    let l:tmp_file = tempname()

    let g:system_async_tasks += [[l:current_file, l:tmp_file, a:ok_callback, a:err_callback, a:data]]
    call SystemAsyncSetUpTimer()

    let l:tmp_file = shellescape(l:tmp_file)

    let l:cmd = a:command
    let l:cmd .= " >" . l:tmp_file .".out"
    let l:cmd .= " 2>" . l:tmp_file . ".err"
    let l:cmd .= " && echo >" . l:tmp_file . ".ok"
    let l:cmd .= " || echo >" . l:tmp_file . ".fail"
    let l:cmd .= " &"

    call system(l:cmd, a:stdin)
endfunction

function! SystemAsyncSetUpTimer()
    if len(g:system_async_tasks) > 0 && g:system_async_timer_set_up == 0
        let g:system_async_timer_set_up = 1
        let g:system_async_orig_updatetime = &updatetime
        set updatetime=1000
        let l:augroup_cmd = "augroup system_async"
        let l:augroup_cmd .= " | execute 'autocmd CursorHold * call SystemAsyncCheckResults()'"
        let l:augroup_cmd .= " | execute 'autocmd CursorHoldI * call SystemAsyncCheckResults()'"
        let l:augroup_cmd .= " | execute 'autocmd CursorMoved * call SystemAsyncCheckResults()'"
        let l:augroup_cmd .= " | execute 'autocmd CursorMovedI * call SystemAsyncCheckResults()'"
        let l:augroup_cmd .= " | execute 'autocmd BufEnter * call SystemAsyncCheckResults()'"
        let l:augroup_cmd .= " | augroup END"
        execute l:augroup_cmd
    endif
endfunction

function! SystemAsyncCheckResults()
    execute "autocmd! system_async CursorHold *"
    execute "autocmd! system_async CursorHoldI *"
    execute "autocmd! system_async CursorMoved *"
    execute "autocmd! system_async CursorMovedI *"
    execute "autocmd! system_async BufEnter *"

    let &updatetime = g:system_async_orig_updatetime
    let g:system_async_timer_set_up = 0

    let l:current_file = expand("%")

    " Iterating over task indices instead of the tasks themselves allows
    " callbacks to adjust data of any upcoming task without relying on how
    " Vimscript handles modifying lists while looping over them.

    let l:new_system_async_task_ids = []
    let l:ok_calls = []
    let l:fail_calls = []

    let l:task_id = 0
    let l:num_tasks = len(g:system_async_tasks)
    let l:num_running = 0
    let l:num_succeeded = 0
    let l:num_failed = 0

    while l:task_id < l:num_tasks
        let l:task = g:system_async_tasks[l:task_id]
        let l:succeeded = 0
        let l:failed = 0

        if filereadable(l:task[1] . ".ok")
            let l:succeeded = 1
            let l:num_succeeded += 1
        else
            if filereadable(l:task[1] . ".fail")
                let l:failed = 1
                let l:num_failed += 1
            endif
        endif

        if l:current_file == l:task[0]
            if l:succeeded != 0
                let l:ok_calls += [l:task_id]
                call delete(l:task[1] . ".ok")
            else
                if l:failed != 0
                    let l:fail_calls += [l:task_id]
                    call delete(l:task[1] . ".fail")
                else
                    let l:new_system_async_task_ids += [l:task_id]
                    let l:num_running += 1
                endif
            endif
        else
            let l:new_system_async_task_ids += [l:task_id]

            if l:succeeded == 0 && l:failed == 0
                let l:num_running += 1
            endif
        endif

        let l:task_id += 1
    endwhile

    let g:system_async_num_running_tasks = l:num_running

    echohl None | echo "Tasks: ok:" . l:num_succeeded . " failed:" . l:num_failed . " running:" . l:num_running

    for l:task_id in l:ok_calls
        let l:task = g:system_async_tasks[l:task_id]
        let l:stdout = readfile(l:task[1] . ".out")
        let l:stderr = readfile(l:task[1] . ".err")
        call delete(l:task[1] . ".out")
        call delete(l:task[1] . ".err")
        call CallFuncByName(l:task[2], l:task[0], l:stdout, l:stderr, l:task[4])
    endfor

    for l:task_id in l:fail_calls
        let l:task = g:system_async_tasks[l:task_id]
        let l:stdout = readfile(l:task[1] . ".out")
        let l:stderr = readfile(l:task[1] . ".err")
        call delete(l:task[1] . ".out")
        call delete(l:task[1] . ".err")
        call CallFuncByName(l:task[3], l:task[0], l:stdout, l:stderr, l:task[4])
    endfor

    let l:new_system_async_tasks = []

    for l:task_id in l:new_system_async_task_ids
        let l:task = g:system_async_tasks[l:task_id]
        let l:new_system_async_tasks += [l:task]
    endfor

    let g:system_async_tasks = l:new_system_async_tasks

    call SystemAsyncSetUpTimer()
endfunction


function! AICatCmd(args)
    let l:console_file = "/dev/tty"

    if has("win32")
        " The redirection to the special console file doesn't work in gVim,
        " so there will be no streaming. At least, it works in a terminal based
        " vim.exe.
        let l:console_file = "CON"
    endif

    " The command will replace the buffer with the stdout while displaying its
    " stderr in the terminal.
    return "ai-cat.py " . a:args . " 2>" . l:console_file
endfunction

" The :AI command will run the current buffer through ai-cat.py (must be on
" PATH) in order to generate a continuation if it looks like an already
" established ai-cat.py conversation, otherwise it will initialize a new
" conversation in a new tab.
function! AICat()
    let l:ai_cat_cmd = "%!" . AICatCmd("stdio")
    let l:cursor_position = getpos(".")

    " Does the currently edited buffer's name look like an ai-cat.py
    " conversation? If the name is empty or ends with .md, then it does.
    let l:may_be_ai_conversation = (expand("%") =~ "^\\(.*\\.md\\)\\?$")

    " Is the buffer an already initialized, ongoing ai-act.py conversation?
    " If it contains block header lines used by ai-act.py, then it is.
    let l:is_ai_conversation = 0

    if l:may_be_ai_conversation
        for l:line_num in range(1, line("$"))
            if getline(l:line_num) =~ "^# === .* ===\\r\\?$"
                let l:is_ai_conversation = 1
                break
            endif
        endfor
    endif

    if l:is_ai_conversation
        " Run the conversation through ai-cat, and put the cursor at the
        " beginning of the last AI, AI Reasoning, or User block or to the end
        " if none of them can be found.

        echohl None | echo "Waiting for AI..."

        execute l:ai_cat_cmd

        if v:shell_error != 0
            undo
            call setpos(".", l:cursor_position)
            return
        endif

        redraw!

        call AIJumpToRelevantBlock()
    else
        " Need to initialize a new conversaion - since this will overwrite the
        " entire buffer, we do it in a new tab if the current one is not empty
        " or its name doesn't look like an ai-cat.py conversaion.

        if line("$") != 1 || getline(1) != "" || !l:may_be_ai_conversation
            tabnew
        endif

        echohl None | echo "Initializing conversation..."

        execute l:ai_cat_cmd
        set filetype=markdown

        if v:shell_error != 0
            undo
            return
        endif

        redraw!
        normal! G
        startinsert
    endif
endfunction
command! -nargs=0 AI call AICat()

function! AIJumpToRelevantBlock()
    let l:response_pos = 0

    for l:line_num in range(line("$"), 1, -1)
        if getline(l:line_num) =~ "^# === \\(AI\\( Reasoning\\)*\\|User\\) ===\\r\\?$"
            let l:response_pos = l:line_num
            break
        endif
    endfor

    if l:response_pos > 0
        call cursor(l:response_pos, 1)
    else
        normal! G
    endif
endfunction

" Add to-do comments to a piece of code, select the relevant lines, then press
" the Tab key to run them through the last used AI in ai-cat.py. If the AI
" requests more information or otherwise fails to produce a usable replacement,
" then the conversation is opened in a new tab for editing. From there, the
" `:AI` command can be used for continuing it. (See above.)
"
" NOTE: only the selected lines and the name of the edited file are sent to the
"       AI, so make sure that they contain all the necessary information.
function! AICatTabReplace() range
    let l:begin_line = line("'<")
    let l:end_line = line("'>")

    if l:begin_line == 0 || l:end_line == 0
        echohl ErrorMsg | echo "Select the lines first to be replaced by AI." | echohl None
        return
    endif

    let l:ai_cat_cmd = AICatCmd("replace " . shellescape(expand("%")))
    let l:input = join(getline(l:begin_line, l:end_line), "\n") . "\n"
    let l:data = [l:begin_line, l:end_line, l:input]

    echohl None | echo "Sending request to AI..."

    call SystemAsync(l:ai_cat_cmd, l:input, "AICatTabReplaceCbOk", "AICatTabReplaceCbErr", l:data)
endfunction
xnoremap <silent> <Tab> :call AICatTabReplace()<CR>

function! AICatTabReplaceCbOk(file_name, stdout, stderr, data)
    let l:begin_line = a:data[0]
    let l:end_line = a:data[1]
    let l:old_lines = a:data[2]

    let l:current_lines = join(getline(l:begin_line, l:end_line), "\n") . "\n"

    if l:old_lines != l:current_lines
        redraw!
        tabnew
        call append(0, a:stdout)
        echo "Conflicting changes in buffer while the AI was working"
        return
    endif

    let l:current_pos = getpos(".")
    let l:current_line = l:current_pos[1]
    let l:current_col = l:current_pos[2]

    execute l:begin_line . "," . l:end_line . "delete _"
    call append(l:begin_line - 1, a:stdout)

    let l:line_num_delta = len(a:stdout) - (l:end_line - l:begin_line + 1)

    if l:begin_line < l:current_line
        let l:current_line += l:line_num_delta
    endif

    let l:task_id = 0
    let l:num_tasks = len(g:system_async_tasks)

    execute "normal! " . l:current_line . "G" . l:current_col . "|"
    redraw!

    while l:task_id < l:num_tasks
        let l:task = g:system_async_tasks[l:task_id]

        if l:task[0] == a:file_name && l:task[2] == "AICatTabReplaceCbOk"
            let l:task_data = l:task[4]

            if l:task_data[1] > l:end_line
                let g:system_async_tasks[l:task_id][4][0] += l:line_num_delta
                let g:system_async_tasks[l:task_id][4][1] += l:line_num_delta
            endif
        endif

        let l:task_id += 1
    endwhile
endfunction

function! AICatTabReplaceCbErr(file_name, stdout, stderr, data)
    redraw!
    tabnew
    set filetype=markdown
    call append(0, a:stderr)
    call append(0, a:stdout)
    call AIJumpToRelevantBlock()
    echo "Failed to get suitable replacemenet, use :AI to continue the conversation after editing"
    return
endfunction
