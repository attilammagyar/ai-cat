#!/bin/bash

# BSD 3-Clause License
#
# Copyright (c) 2026, Attila Magyar
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


set -e
set -o pipefail


main()
{
    local cache
    local model
    local reasoning

    while read
    do
        echo ""
        echo "####################################################"
        echo "# TESTING WITH $REPLY"
        echo "####################################################"
        echo ""

        cache="$(printf "%s" "$REPLY" | cut -d" " -f1)"
        reasoning="$(printf "%s" "$REPLY" | cut -d" " -f2)"
        model="$(printf "%s" "$REPLY" | cut -d" " -f3)"

        python3 ai-cat.py stdio <<CONV
# === System ===

Please respond as a helpful AI assistant.

# === Settings ===

Cache: $cache
Model: $model
Reasoning: $reasoning
Streaming: off
Temperature: 1.0

# === User ===

Please explain in a brief sentence why the sky is blue.

# === AI ===

Because it's a giant dome and blue paint happened to be cheap when it was built.

# === User ===

Thanks. Now repeat that but talk like a pirate.

CONV
    done <<MODELS
on off anthropic/claude-haiku-4-5-20251001
on off deepseek/deepseek-v4-flash
on off google/gemini-2.5-flash
on off mistral/mistral-small-latest
default default openai/gpt-4.1
on off openai/gpt-5.6-luna
on off perplexity/sonar
on off xai/grok-4.3
MODELS
}

main "$@"
