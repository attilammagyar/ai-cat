ai-cat.py
=========

`ai-cat.py` is a command-line API client application to access a few popular
[LLM](https://en.wikipedia.org/wiki/Large_language_model) providers.

Its features include:

 * A system prompt which sets up a sassy, wisecracking AI assistant that has a
   knack for programming and [STEM](https://en.wikipedia.org/wiki/Science,_technology,_engineering,_and_mathematics)
   problem solving.

 * Precise control over model selection,
   [sampling temperature](https://en.wikipedia.org/wiki/Softmax_function),
   reasoning, etc.

 * Allows editing the entire conversation in Markdown, including the AI's
   responses. (Useful for nudging the autoregressive text generation process.)

 * Works as a standalone interactive CLI app or as a standard Unix filter that
   can be integrated with editors like Vim.

 * Can connect to the API of:

    * [Anthropic](https://www.anthropic.com/),
    * [DeepSeek](https://www.deepseek.com/en),
    * [Google](https://gemini.google.com/),
    * [OpenAI](https://openai.com/),
    * and [Perplexity](https://www.perplexity.ai/).

### Setting up ai-cat.py

To use `ai-cat.py`, you need to generate an API key for at least one of the
supported AI providers, and save it in `~/.ai-py` in the following format
(delete the ones that you don't want to use):

    {
      "api_keys": {
        "anthropic": "Anthropic Claude API key here (https://console.anthropic.com/settings/keys)",
        "deepseek": "DeepSeek R1 API key here (https://platform.deepseek.com/api_keys)",
        "google": "Google Gemini API key here (https://aistudio.google.com/apikey)",
        "openai": "OpenAI ChatGPT API key here (https://platform.openai.com/settings/organization/api-keys)",
        "perplexity": "Perplexity API key here (https://www.perplexity.ai/account/api/keys)"
      }
    }
