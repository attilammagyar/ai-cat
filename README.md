ai-cat.py
=========

A simple and stupid, [Vim](https://www.vim.org/)-friendly,
[Markdown](https://en.wikipedia.org/wiki/Markdown)-based command-line client
for popular [LLM](https://en.wikipedia.org/wiki/Large_language_model) AI
chatbot APIs, written in [Python](https://www.python.org/).

```sh
$ ai-cat.py <<EOF
# === System ===
Please act as a helpful AI assistant.

# === Settings ===
Model: openai/gpt-4.1

# === User ===
Please explain in a brief sentence why the sky is blue.

# === AI ===
The sky is blue because molecules in the Earth's atmosphere scatter
shorter-wavelength blue light from the sun more than they scatter
longer-wavelength red light.

# === User ===
Say that again but talk like a pirate.

EOF
```

(`ai-cat` as in the name of the Unix/Linux tool
[cat](https://en.wikipedia.org/wiki/Cat_%28Unix%29), because it
_concatenates_ the AI's response to the end of a conversation.)

Demo
----

### Chat in Vim

<img src="https://raw.githubusercontent.com/attilammagyar/ai-cat/main/images/ai-cat-py-vim.gif" alt="ai-cat.py stdin/stdout chat, integrated into Vim" />

### Code replacement in Vim

<img src="https://raw.githubusercontent.com/attilammagyar/ai-cat/main/images/ai-cat-py-vim-replace.gif" alt="ai-cat.py performing code replacement in Vim" />

### As an interactive CLI app

<img src="https://raw.githubusercontent.com/attilammagyar/ai-cat/main/images/ai-cat-py-interactive.gif" alt="ai-cat.py running as an interactive CLI app" />

Features
--------

 * A default system prompt which sets up a sassy, wisecracking AI assistant
   that has a knack for programming and [STEM](https://en.wikipedia.org/wiki/Science,_technology,_engineering,_and_mathematics)
   problem solving.

 * Precise control over model selection,
   [sampling temperature](https://en.wikipedia.org/wiki/Softmax_function),
   reasoning, etc. Can switch models even in the middle of a conversation.

 * Allows editing the entire conversation, including the AI's previous
   responses. (Useful for steering and nudging the autoregressive text
   generation process if necessary.)

 * Simple, Markdown-based syntax.

 * Works as a standalone interactive CLI app or as an stdin/stdout filter
   that can be integrated nicely with other programs (e.g. Vim):

    * To use the **interactive mode**, run `ai-cat.py interactive` (this is the
      default when the standard input is a TTY).

    * To use the **filter mode**, run `ai-cat.py stdio` (this is the default
      when the standard input is not a TTY).

    * The **replace mode** (`ai-cat.py replace`) can be used for implementing
      simple and crude AI-aided code editing in  any scriptable text editor
      (e.g. Vim):

       * the lines that are supplied over the standard input are sent to the
         AI,

       * the model figures out what needs to be done (e.g. implement `TODO`
         comments, add header docs, etc.),

       * the result is printed to the standard output,

       * the exit code tells how to process it:

          * `0` means that the AI successfully generated a replacement for the
            given lines.

          * `1` means that the AI needs more information and wants to start a
            discussion - in this case, the standard output will contain an
            entire `ai-cat.py` conversation in Markdown.

          * `2` and everything else means that an error occurred, check the
            standard error for the details.

 * Can connect to the API of:

    * [Anthropic (Claude)](https://www.anthropic.com/),
    * [DeepSeek](https://www.deepseek.com/en),
    * [Google (Gemini)](https://gemini.google.com/),
    * [OpenAI (ChatGTP)](https://openai.com/),
    * [Perplexity (Sonar)](https://www.perplexity.ai/),
    * and [xAI (Grok)](https://x.ai/).

Dependencies
------------

None. Only built-in Python modules.

Setting up before the first use
-------------------------------

Place `ai-cat.py` to a location where your system can find and run it using
Python. Adjust your `PATH` variable if necessary.

To use `ai-cat.py`, you need to generate an API key for at least one of the
supported AI providers, and save it in `~/.ai-cat` (or
`C:\Users\<NAME>\_ai-cat` on Windows) in the following format:

```json
{
  "api_keys": {
    "anthropic": "Anthropic Claude API key here (https://console.anthropic.com/settings/keys)",
    "deepseek": "DeepSeek R1 API key here (https://platform.deepseek.com/api_keys)",
    "google": "Google Gemini API key here (https://aistudio.google.com/apikey)",
    "openai": "OpenAI ChatGPT API key here (https://platform.openai.com/settings/organization/api-keys)",
    "perplexity": "Perplexity API key here (https://www.perplexity.ai/account/api/keys)",
    "xai": "xAI API key here (https://console.x.ai/team/default/api-keys)"
  }
}
```

(Delete the ones that you don't want to use.)

Alternatively, you can leave the `api_keys` object empty, and provide the API
keys via the following environment variables as well:

 * `ANTHROPIC_API_KEY`,
 * `DEEPSEEK_API_KEY`,
 * `GEMINI_API_KEY`,
 * `OPENAI_API_KEY`,
 * `PERPLEXITY_API_KEY`,
 * `XAI_API_KEY`.

The `EDITOR` environment variable can be used for customizing what text editor
will be launched in interactive mode to edit the conversation before sending it
to the AI for completion. Your preferred default editor (which will be sued
when the `EDITOR` variable is not set) can also be specified next to the API
keys:

```
{
  "api_keys": { ... },
  "editor": "vim"
}
```

Conversation syntax
-------------------

A conversation is a sequence of text blocks that are separated by specially
formatted level 1 Markdown header lines. The header lines tell `ai-cat.py` how
to process each block.

A basic conversation after a few turns may look like the following:

```md
# === System ===

Please act as a helpful AI assistant.

# === Settings ===

Model: openai/gpt-4.1
Reasoning: default
Streaming: on
Temperature: 1.0

# === User ===

Please explain why the sky is blue.

# === AI ===

Because the air scatters the blue light more than the other colors.

# === User ===

Say that again but talk like a pirate.

# === AI ===

Yarr, 'tis 'cause th' air be scatterin' th' blue light more'n all th' other
colors, savy?
```

The `System` block contains general behavioural instructions for the model,
a.k.a. the *system prompt*. It is always automatically moved to the beginning
of the conversation, and when multiple `System` blocks are specified, only the
last one is kept. When it is omitted, then the built-in system prompt from
`ai-cat.py` is used.

When the last block in a conversation is a `User` block, then `ai-cat.py` will
send the conversation to the selected LLM and generate a response for it.

If the optional `Settings` block or any of the settings in it are omitted, then
the values from the last `ai-cat.py` interaction are used. Subsequent `Setting`
blocks and settings overwrite each other.

`ai-cat.py` also adds additional information blocks to the conversation:

 * `Notes`: a few tips for using `ai-cat.py`, and a complete list of the
   available models from the configured providers.

 * `AI Reasoning`: the chain-of-thought tokens or summaries generated by large
    reasoning models.

 * `AI Status`: token usage and other API-specific status info.

These are included only for convenience and as diagnostic information, but are
never sent back to the AI.

If `ai-cat.py` is used in `stdio` mode and the standard input is empty, then
it will generate an empty conversation template, including its default system
prompt.

Vim integration
---------------

### Chat and code editing

The `~/.vimrc` snippet below (or `_vimrc` for Windows users) sets up the
`:AI` command to either initialize a new conversation or run an existing one
through `ai-cat.py`, depending on the contents of the current buffer. (Make
sure that your `PATH` is set up correctly so that `ai-cat.py` can be run, or
adjust the snippet to fit your environment.) It works best when Vim is running
in a terminal.

It also sets up a very minimalistic and crude code generator:

 * add to-do comments to a piece of code,

 * select all the relevant lines in Visual mode,

 * then press the `Tab` key to run them through `ai-cat.py` with the last used
   settings, and replace them automatically with the result.

If the AI needs more information or otherwise fails to produce a usable
replacement for the selected lines, then the conversation is opened in a new
tab for editing which then can be continued using the `:AI` command.

The advantage of this approach is that you get precise manual control over what
is sent to the AI. The disadvantage is that you *have to precisely control
manually what is sent to the AI*. No context, no codebase indexing, no
[LSP](https://en.wikipedia.org/wiki/Language_Server_Protocol) integration, no
nothing.

```vim
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
" `:AI` command can be used to continue it. (See above.)
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

    echohl None | echo "Waiting for AI..."

    let l:ai_cat_cmd = AICatCmd("replace " . shellescape(expand("%")))
    let l:input = join(getline(l:begin_line, l:end_line), "\n") . "\n"
    let l:output = system(l:ai_cat_cmd, l:input)

    if v:shell_error != 0
        if v:shell_error == 1
            redraw!
            tabnew
            set filetype=markdown
            call append(0, split(l:output, "\n", 1))
            call AIJumpToRelevantBlock()
            echo "The AI needs more info, use :AI to continue the conversation"
            return
        endif

        echohl ErrorMsg | echo "Error running ai-cat.py" | echohl None
        call input("", "Press ENTER to continue.")
        redraw!
        return
    endif

    execute l:begin_line . "," . l:end_line . "delete _"
    call append(l:begin_line - 1, split(l:output, "\n", 1))
    execute "normal! " . l:begin_line . "G"
    redraw!
endfunction
xnoremap <silent> <Tab> :call AICatTabReplace()<CR>
```

### Select text between Markdown code fences

When using AI for coding, the Vimscript snippet below may also be useful:
the `vI` (`v` followed by Shift + `i`) hotkey in Normal mode will select all
lines between the first Markdown code fence above and below the cursor. (The
`v` key triggers Visual mode, the `I` key calls the
`SelectBetweenMarkdownFences()` function.)

```vim
" Pressing I (Shift+i) in Visual mode will select everything between the
" previous and the next Markdown code fence. (Does not handle code blocks
" that are nested inside other elements like list items or block quotes.)
function! SelectBetweenMarkdownFences()
    let l:current_line = line(".")
    let l:begin = 1
    let l:end = line("$")

    " Could use search("^```", "Wbcn") and search("^```", "Wn"), but that would
    " mess up the search history.

    for l:line_num in range(l:current_line, 1, -1)
        if getline(l:line_num) =~ "^```"
            let l:begin = l:line_num + 1
            break
        endif
    endfor

    for l:line_num in range(l:current_line + 1, line("$"))
        if getline(l:line_num) =~ "^```"
            let l:end = l:line_num - 1
            break
        endif
    endfor

    if l:begin > l:end
        return
    endif

    execute "normal! " . l:begin . "Gv" . l:end . "G$"
endfunction
xnoremap <silent> I :call SelectBetweenMarkdownFences()<CR>
```

But why?
--------

It's intended to solve my complaints against existing solutions:

1. I'm not a fan of digital feudalism and the subscription based economy, and I
   avoid it like the plague. Prepaid API credits are somewhat closer to my
   heart.

2. GUIs and agents: limited to no control over model selection, system prompt,
   etc.

3. Agents: if I have to keep an eye on what they are doing, then they don't
   seem to be that much of a speed up. But I'm also not comfortable with
   leaving them to work alone, changing files and running arbitrary commands
   based on a stochastic process, regardless of how sophisticated that may be.

4. You get good at what you practise, and you lose skills that you don't.
   Therefore I try to limit my AI usage to only the boring parts of programming
   (e.g. cookie-cutter UI stuff, boilerplate, etc.), and to get my work
   reviewed.

5. There is undeniably a hype in the industry right now (as of August, 2025).
   When the music stops and the VC money dries up, several products will go
   down, others will get heavily [enshittified](https://en.wikipedia.org/wiki/Enshittification).
   Developing a reliance on any particular service (see also: [vendor
   lock-in](https://en.wikipedia.org/wiki/Vendor_lock-in)) risks future pain
   and disappointment.

6. AFAIK the legal status of AI generated code is still unclear (as of August,
   2025): can you put large chunks of it in open source (e.g. GPL) or
   proprietary projects?  How much do you have to modify it before you can?
   Where's the threshold of originality?  Do you have to include the prompts as
   well?

7. The default AI persona drives me nuts with its excessive sugarcoating and
   politeness.

8. I've switched to Vim around 2011 and never looked back. IDEs came and went
   over the years (Eclipse, NetBeans, IntelliJ, Sublime, VS Code, etc.), but so
   far nothing has beaten Vim in terms of value vs. cost, especially with its
   stellar scriptability and macros. I don't see a reason for this to change
   any time soon.
