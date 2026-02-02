#!/usr/bin/env python3

# BSD 3-Clause License
#
# Copyright (c) 2025, Attila Magyar
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

import collections.abc
import importlib
import os
import sys
import typing
import unittest


ai_cat = importlib.import_module("ai-cat")


class TestGetItem(unittest.TestCase):
    def test_get_item(self):
        container = {"aaa": [{"bbb": "42", "ccc": 123}]}

        self.assertEqual("42", ai_cat.get_item(container, "aaa.0.bbb"))
        self.assertEqual(123, ai_cat.get_item(container, "aaa.0.ccc", expect_type=int))
        self.assertIsNone(ai_cat.get_item(container, "aaa.2.zzz"))
        self.assertIsNone(ai_cat.get_item(container, "aaa.0.ccc", expect_type=str))
        self.assertEqual(
            "default",
            ai_cat.get_item(container, "aaa.2.zzz", default="default"),
        )
        self.assertEqual(
            "default",
            ai_cat.get_item(container, "aaa.0.ccc", default="default", expect_type=str),
        )


class TestAiMessenger(unittest.TestCase):
    NOTES = ai_cat.AiMessenger.NOTES_HEADER + """\
 * fake/model1
 * fake/model2"""

    LONG_CONVERSATION = """\
# === System ===

Custom system prompt.


# === Settings ===

Model: fake/model2
Reasoning: on
Streaming: on
Temperature: 2.0


# === User ===

What is a question?


# === AI Reasoning ===

Something similar to that sentence, just not as dumb.


# === AI ===

A sentence seeking an answer.


# === AI Status ===

Status info, stop reason, etc. here.


# === User ===

And what is The Answer?"""

    maxDiff = None

    @staticmethod
    def create_messenger(
            responses: collections.abc.Sequence[collections.abc.Sequence[ai_cat.AiResponse]]=[],
    ) -> tuple[ai_cat.AiMessenger, ai_cat.AiClient]:
        ai_client = FakeAiClient(responses)
        ai_messenger = ai_cat.AiMessenger(
            {"fake": ai_client},
            [f"fake/{model}" for model in ai_client.list_models()]
        )

        return (ai_messenger, ai_client)

    @classmethod
    def ask(
            cls,
            edited_conversation: str,
            responses: collections.abc.Sequence[collections.abc.Sequence[ai_cat.AiResponse]],
    ) -> tuple[ai_cat.AiMessenger, ai_cat.AiClient, collections.abc.Sequence[str]]:
        ai_messenger, ai_client = cls.create_messenger(responses)
        response_chunks = list(
            ai_messenger.ask(
                "dummy question",
                lambda conversation: edited_conversation
            )
        )

        return (ai_messenger, ai_client, response_chunks)

    def test_filter_models_by_prefix(self):
        ai_messenger = self.create_messenger()[0]

        self.assertEqual([], ai_messenger.filter_models_by_prefix("bake/"))
        self.assertEqual(
            ["fake/model1"],
            ai_messenger.filter_models_by_prefix("fake/model1")
        )
        self.assertEqual(
            ["fake/model1", "fake/model2"],
            ai_messenger.filter_models_by_prefix("fake/")
        )

    def test_model_setting_is_validated(self):
        ai_messenger = self.create_messenger()[0]

        ai_messenger.set_model("fake/model1")
        model_1 = ai_messenger.get_model()
        model_info_1 = ai_messenger.get_model_info()
        ai_messenger.set_model("fake/model2")
        model_2 = ai_messenger.get_model()
        model_info_2 = ai_messenger.get_model_info()

        self.assertRaises(ValueError, ai_messenger.set_model, "bake/model1")
        self.assertRaises(ValueError, ai_messenger.set_model, "fake/model99")
        self.assertEqual("fake/model1", model_1)
        self.assertEqual("Model: fake/model1", model_info_1)
        self.assertEqual("fake/model2", model_2)
        self.assertEqual("Model: fake/model2", model_info_2)

    def test_reasoning_setting_is_validated(self):
        ai_messenger = self.create_messenger()[0]

        ai_messenger.set_reasoning("Default")
        reasoning_1 = ai_messenger.get_reasoning()
        reasoning_info_1 = ai_messenger.get_reasoning_info()
        ai_messenger.set_reasoning("on")
        reasoning_2 = ai_messenger.get_reasoning()
        reasoning_info_2 = ai_messenger.get_reasoning_info()
        ai_messenger.set_reasoning("off")
        reasoning_3 = ai_messenger.get_reasoning()
        reasoning_info_3 = ai_messenger.get_reasoning_info()

        self.assertRaises(ValueError, ai_messenger.set_reasoning, "no")
        self.assertRaises(ValueError, ai_messenger.set_reasoning, "yes")
        self.assertEqual("default", reasoning_1)
        self.assertEqual("Reasoning: default", reasoning_info_1)
        self.assertEqual("on", reasoning_2)
        self.assertEqual("Reasoning: on", reasoning_info_2)
        self.assertEqual("off", reasoning_3)
        self.assertEqual("Reasoning: off", reasoning_info_3)

    def test_streaming_setting_is_validated(self):
        ai_messenger = self.create_messenger()[0]

        ai_messenger.set_streaming("On")
        streaming_1 = ai_messenger.get_streaming()
        streaming_info_1 = ai_messenger.get_streaming_info()
        ai_messenger.set_streaming("off")
        streaming_2 = ai_messenger.get_streaming()
        streaming_info_2 = ai_messenger.get_streaming_info()

        self.assertRaises(ValueError, ai_messenger.set_streaming, "no")
        self.assertRaises(ValueError, ai_messenger.set_streaming, "yes")
        self.assertEqual("on", streaming_1)
        self.assertEqual("Streaming: on", streaming_info_1)
        self.assertEqual("off", streaming_2)
        self.assertEqual("Streaming: off", streaming_info_2)

    def test_temperature_setting_is_validated(self):
        ai_messenger = self.create_messenger()[0]

        ai_messenger.set_temperature(2.0)
        temperature_1 = ai_messenger.get_temperature()
        temperature_info_1 = ai_messenger.get_temperature_info()
        ai_messenger.set_temperature(0.0)
        temperature_2 = ai_messenger.get_temperature()
        temperature_info_2 = ai_messenger.get_temperature_info()

        self.assertRaises(ValueError, ai_messenger.set_temperature, 999.0)
        self.assertRaises(ValueError, ai_messenger.set_temperature, float("nan"))
        self.assertEqual(2.0, temperature_1)
        self.assertEqual("Temperature: 2.0", temperature_info_1)
        self.assertEqual(0.0, temperature_2)
        self.assertEqual("Temperature: 0.0", temperature_info_2)

    def test_unknown_blocks_raise_error(self):
        ai_messenger = self.create_messenger()[0]

        edited_conversation = """\
# === Usre ===

What is The Answer?
"""
        self.assertRaises(
            ValueError,
            list,
            ai_messenger.ask(
                "dummy_question",
                lambda conversation: edited_conversation,
            ),
        )

    def test_unknown_settings_raise_error(self):
        ai_messenger = self.create_messenger()[0]

        edited_conversation = """\
# === Settings ===

Tmperature: 1.0

# === User ===

What is The Answer?
"""
        self.assertRaises(
            ValueError,
            list,
            ai_messenger.ask(
                "dummy_question",
                lambda conversation: edited_conversation,
            ),
        )

    def test_initial_conversation_is_populated_with_defaults(self):
        ai_messenger = self.create_messenger()[0]

        expected_conversation = f"""\
{self.NOTES}

# === System ===

{ai_cat.DEFAULT_SYSTEM_PROMPT}


# === Settings ===

Model: fake/model1
Reasoning: default
Streaming: off
Temperature: {ai_cat.AiMessenger.DEFAULT_TEMPERATURE}



# === User ===


"""
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())

    def test_initial_conversation_reflects_the_current_settings(self):
        ai_messenger = self.create_messenger()[0]

        ai_messenger.set_model("fake/model2")
        ai_messenger.set_reasoning(ai_cat.Reasoning.ON.value)
        ai_messenger.set_streaming(ai_cat.Streaming.OFF.value)
        ai_messenger.set_temperature(2.0)

        expected_conversation = f"""\
{self.NOTES}

# === System ===

{ai_cat.DEFAULT_SYSTEM_PROMPT}


# === Settings ===

Model: fake/model2
Reasoning: on
Streaming: off
Temperature: 2.0



# === User ===


"""
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())

    def test_empty_edited_conversation_is_ignored_but_existing_conversation_is_kept(self):
        empty_conversation = "\n"
        ai_messenger, ai_client, response_chunks = self.ask(
            self.LONG_CONVERSATION,
            [
                [
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=False, text="42."),
                ],
            ],
        )
        ai_client.model = None
        ai_client.conversation = None
        ai_client.temperature = None
        ai_client.reasoning = None
        ai_client.streaming = None

        response_chunks = list(
            ai_messenger.ask(
                "dummy question",
                lambda conversation: empty_conversation
            )
        )

        expected_conversation = f"""\
{self.NOTES}

{self.LONG_CONVERSATION}


# === AI ===

42.
"""
        self.assertEqual([], response_chunks)
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())
        self.assertIsNone(ai_client.model)
        self.assertIsNone(ai_client.conversation)
        self.assertIsNone(ai_client.temperature)
        self.assertIsNone(ai_client.reasoning)
        self.assertIsNone(ai_client.streaming)

    def test_ai_response_can_be_streamed_and_appended_to_the_conversation(self):
        ai_messenger, ai_client, response_chunks = self.ask(
            self.LONG_CONVERSATION,
            [
                [
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=False, text="42."),
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=True, text="Status info 1 here."),
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=True, text="Status info 2 here."),
                ],
            ],
        )

        expected_conversation = f"""\
{self.NOTES}

{self.LONG_CONVERSATION}


# === AI ===

42.


# === AI Status ===

Status info 1 here.

Status info 2 here.
"""
        self.assertEqual(
            [
                "Model: fake/model2\n",
                "Reasoning: on\n",
                "Streaming: on\n",
                "Temperature: 2.0\n",
                "Waiting for fake...",
                "\n\n# === AI ===\n\n",
                "42.",
                "\n",
                "\n# === AI Status ===\n\nStatus info 1 here.\n\nStatus info 2 here.\n",
            ],
            response_chunks,
        )
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())
        self.assertEqual("model2", ai_client.model)
        self.assertEqual(
            [
                ai_cat.Message(type=ai_cat.MessageType.SYSTEM, text="Custom system prompt."),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="What is a question?"),
                ai_cat.Message(type=ai_cat.MessageType.AI, text="A sentence seeking an answer."),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="And what is The Answer?"),
            ],
            ai_client.conversation,
        )
        self.assertEqual(2.0, ai_client.temperature)
        self.assertEqual(ai_cat.Reasoning.ON, ai_client.reasoning)
        self.assertEqual(True, ai_client.streaming)

    def test_when_the_edited_conversation_lacks_a_system_prompt_then_the_default_is_used(self):
        edited_conversation = "# === User ===\n\nWhat is The Answer?"

        ai_messenger, ai_client, response_chunks = self.ask(
            edited_conversation,
            [
                [
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=False, text="42."),
                ],
            ],
        )

        expected_conversation = f"""\
{self.NOTES}

# === System ===

{ai_cat.DEFAULT_SYSTEM_PROMPT}


{edited_conversation}


# === AI ===

42.
"""
        self.assertEqual(
            [
                "Waiting for fake...",
                "\n\n# === AI ===\n\n",
                "42.",
                "\n",
            ],
            response_chunks,
        )
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())
        self.assertEqual("model1", ai_client.model)
        self.assertEqual(ai_cat.AiMessenger.DEFAULT_TEMPERATURE, ai_client.temperature)
        self.assertEqual(
            [
                ai_cat.Message(type=ai_cat.MessageType.SYSTEM, text=ai_cat.DEFAULT_SYSTEM_PROMPT),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="What is The Answer?"),
            ],
            ai_client.conversation,
        )

    def test_the_system_block_is_moved_to_the_beginning_of_the_conversation(self):
        edited_conversation = """\
# === User ===

What is The Answer?

# === System ===

Please act as a helpful AI assistant.
"""

        ai_messenger, ai_client, response_chunks = self.ask(
            edited_conversation,
            [
                [
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=False, text="42."),
                ],
            ],
        )

        expected_conversation = f"""\
{self.NOTES}

# === System ===

Please act as a helpful AI assistant.


# === User ===

What is The Answer?


# === AI ===

42.
"""
        self.assertEqual(
            [
                "Waiting for fake...",
                "\n\n# === AI ===\n\n",
                "42.",
                "\n",
            ],
            response_chunks,
        )
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())
        self.assertEqual("model1", ai_client.model)
        self.assertEqual(ai_cat.AiMessenger.DEFAULT_TEMPERATURE, ai_client.temperature)
        self.assertEqual(
            [
                ai_cat.Message(
                    type=ai_cat.MessageType.SYSTEM,
                    text="Please act as a helpful AI assistant.",
                ),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="What is The Answer?"),
            ],
            ai_client.conversation,
        )

    def test_when_a_conversation_has_multile_system_prompts_then_only_the_last_one_is_kept(self):
        edited_conversation = """\
# === System ===

This gets dropped.

# === User ===

What is The Answer?

# === System ===

Please act as a helpful AI assistant.
"""

        ai_messenger, ai_client, response_chunks = self.ask(
            edited_conversation,
            [
                [
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=False, text="42."),
                ],
            ],
        )

        expected_conversation = f"""\
{self.NOTES}

# === System ===

Please act as a helpful AI assistant.


# === User ===

What is The Answer?


# === AI ===

42.
"""
        self.assertEqual(
            [
                "Waiting for fake...",
                "\n\n# === AI ===\n\n",
                "42.",
                "\n",
            ],
            response_chunks,
        )
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())
        self.assertEqual("model1", ai_client.model)
        self.assertEqual(ai_cat.AiMessenger.DEFAULT_TEMPERATURE, ai_client.temperature)
        self.assertEqual(
            [
                ai_cat.Message(
                    type=ai_cat.MessageType.SYSTEM,
                    text="Please act as a helpful AI assistant.",
                ),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="What is The Answer?"),
            ],
            ai_client.conversation,
        )

    def test_when_the_edited_conversation_lacks_a_settings_block_then_the_current_settings_are_used(self):
        edited_conversation = """\
# === System ===

Custom system prompt.


# === User ===

What is The Answer?
"""
        ai_messenger, ai_client = self.create_messenger(
            [
                [
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=False, text="42."),
                ],
            ],
        )
        ai_messenger.set_model("fake/model2")
        ai_messenger.set_reasoning(ai_cat.Reasoning.OFF.value)
        ai_messenger.set_streaming(ai_cat.Streaming.OFF.value)
        ai_messenger.set_temperature(2.0)
        ai_messenger.clear()

        response_chunks = list(
            ai_messenger.ask(
                "dummy question",
                lambda conversation: edited_conversation
            )
        )

        expected_conversation = f"""\
{self.NOTES}

{edited_conversation}

# === AI ===

42.
"""
        self.assertEqual(
            [
                "Waiting for fake...",
                "\n\n# === AI ===\n\n",
                "42.",
                "\n",
            ],
            response_chunks,
        )
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())
        self.assertEqual("model2", ai_client.model)
        self.assertEqual(
            [
                ai_cat.Message(type=ai_cat.MessageType.SYSTEM, text="Custom system prompt."),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="What is The Answer?"),
            ],
            ai_client.conversation,
        )
        self.assertEqual(2.0, ai_client.temperature)
        self.assertEqual(ai_cat.Reasoning.OFF, ai_client.reasoning)
        self.assertEqual(False, ai_client.streaming)

    def test_when_the_edited_conversation_does_not_end_with_user_prompt_then_no_ai_response_is_created_but_conversation_is_saved(self):
        edited_conversation = """\
# === System ===

Custom system prompt.


# === User ===

What is The Answer?


# === AI ===

42."""
        ai_messenger, ai_client, response_chunks = self.ask(
            edited_conversation,
            [[]],
        )

        expected_conversation = f"""\
{self.NOTES}

{edited_conversation}
"""
        self.assertEqual([], response_chunks)
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())
        self.assertIsNone(ai_client.model)
        self.assertIsNone(ai_client.conversation)
        self.assertIsNone(ai_client.temperature)
        self.assertIsNone(ai_client.reasoning)
        self.assertIsNone(ai_client.streaming)

    def test_clearing_resets_the_system_prompt_but_keeps_settings(self):
        ai_messenger = self.ask(
            self.LONG_CONVERSATION,
            [
                [
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=False, text="42."),
                ],
            ],
        )[0]
        ai_messenger.set_reasoning(ai_cat.Reasoning.OFF.value)
        ai_messenger.set_streaming(ai_cat.Streaming.OFF.value)

        ai_messenger.clear()

        expected_conversation = f"""\
{self.NOTES}

# === System ===

{ai_cat.DEFAULT_SYSTEM_PROMPT}


# === Settings ===

Model: fake/model2
Reasoning: off
Streaming: off
Temperature: 2.0



# === User ===


"""
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())

    def test_when_the_edited_conversation_lacks_a_user_prompt_when_conversation_is_reset(self):
        edited_conversation = """\
# === System ===

Custom system prompt.


# === AI ===

42.
"""
        ai_messenger, ai_client = self.create_messenger()
        ai_messenger.set_model("fake/model2")
        ai_messenger.set_temperature(2.0)
        ai_messenger.set_reasoning(ai_cat.Reasoning.OFF.value)
        ai_messenger.set_streaming(ai_cat.Streaming.OFF.value)
        ai_messenger.clear()

        response_chunks = list(
            ai_messenger.ask(
                "dummy question",
                lambda conversation: edited_conversation
            )
        )

        expected_conversation = f"""\
{self.NOTES}

# === System ===

Custom system prompt.


# === Settings ===

Model: fake/model2
Reasoning: off
Streaming: off
Temperature: 2.0



# === User ===


"""
        self.assertEqual([], response_chunks)
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())
        self.assertIsNone(ai_client.model)
        self.assertIsNone(ai_client.conversation)
        self.assertIsNone(ai_client.reasoning)
        self.assertIsNone(ai_client.streaming)
        self.assertIsNone(ai_client.temperature)

    def test_block_headers_are_ignored_inside_fenced_code_blocks(self):
        system_prompt = """\
Custom system prompt.

```
# === What ===

Not an actual block.
```

 * list item 1
 * list item 2

   1. sub-list
      ```python
      print('''
      # === Code block inside nested list items
      ''')
      ```\
"""
        conversation = f"""\
# === System ===

{system_prompt}


# === Settings ===

Temperature: 2.0


# === User ===

What is The Answer?
"""
        ai_messenger, ai_client, response_chunks = self.ask(
            conversation,
            [
                [
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=False, text="42."),
                ],
            ],
        )

        expected_conversation = f"""\
{self.NOTES}

{conversation}

# === AI ===

42.
"""
        self.assertEqual(
            [
                "Temperature: 2.0\n",
                "Waiting for fake...",
                "\n\n# === AI ===\n\n",
                "42.",
                "\n",
            ],
            response_chunks,
        )
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())
        self.assertEqual(
            [
                ai_cat.Message(type=ai_cat.MessageType.SYSTEM, text=system_prompt),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="What is The Answer?"),
            ],
            ai_client.conversation,
        )
        self.assertEqual(2.0, ai_client.temperature)

    def test_ai_reasoning_and_response_can_be_streamed_and_appended_to_the_conversation(self):
        ai_messenger, ai_client, response_chunks = self.ask(
            self.LONG_CONVERSATION,
            [
                [
                    ai_cat.AiResponse(is_delta=True, is_reasoning=True, is_status=False, text="6*9"),
                    ai_cat.AiResponse(is_delta=True, is_reasoning=True, is_status=False, text=" which is 42"),
                    ai_cat.AiResponse(is_delta=True, is_reasoning=True, is_status=False, text=" in base 13."),
                    ai_cat.AiResponse(is_delta=True, is_reasoning=False, is_status=False, text="4"),
                    ai_cat.AiResponse(is_delta=True, is_reasoning=False, is_status=False, text="2"),
                    ai_cat.AiResponse(is_delta=True, is_reasoning=False, is_status=False, text="."),
                ],
            ],
        )

        expected_conversation = f"""\
{self.NOTES}

{self.LONG_CONVERSATION}


# === AI Reasoning ===

6*9 which is 42 in base 13.


# === AI ===

42.
"""
        self.assertEqual(
            [
                "Model: fake/model2\n",
                "Reasoning: on\n",
                "Streaming: on\n",
                "Temperature: 2.0\n",
                "Waiting for fake...",
                "\n\n# === AI Reasoning ===\n\n",
                "6*9",
                " which is 42",
                " in base 13.",
                "\n\n# === AI ===\n\n",
                "4",
                "2",
                ".",
                "\n",
            ],
            response_chunks,
        )
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())
        self.assertEqual("model2", ai_client.model)
        self.assertEqual(
            [
                ai_cat.Message(type=ai_cat.MessageType.SYSTEM, text="Custom system prompt."),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="What is a question?"),
                ai_cat.Message(type=ai_cat.MessageType.AI, text="A sentence seeking an answer."),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="And what is The Answer?"),
            ],
            ai_client.conversation,
        )
        self.assertEqual(2.0, ai_client.temperature)
        self.assertEqual(ai_cat.Reasoning.ON, ai_client.reasoning)
        self.assertEqual(True, ai_client.streaming)

    def test_when_the_ai_provides_complete_reasoning_and_response_after_a_stream_then_they_are_appended_to_the_conversation(self):
        ai_messenger, ai_client, response_chunks = self.ask(
            self.LONG_CONVERSATION,
            [
                [
                    ai_cat.AiResponse(is_delta=True, is_reasoning=True, is_status=False, text="6*9"),
                    ai_cat.AiResponse(is_delta=True, is_reasoning=True, is_status=False, text=" which is 42"),
                    ai_cat.AiResponse(is_delta=True, is_reasoning=True, is_status=False, text=" in base 13."),
                    ai_cat.AiResponse(is_delta=False, is_reasoning=True, is_status=False, text="The answer is 42."),
                    ai_cat.AiResponse(is_delta=True, is_reasoning=False, is_status=False, text="6"),
                    ai_cat.AiResponse(is_delta=True, is_reasoning=False, is_status=False, text="*"),
                    ai_cat.AiResponse(is_delta=True, is_reasoning=False, is_status=False, text="9"),
                    ai_cat.AiResponse(is_delta=True, is_reasoning=False, is_status=False, text="."),
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=False, text="42."),
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=True, text="Status info here."),
                ],
            ],
        )

        expected_conversation = f"""\
{self.NOTES}

{self.LONG_CONVERSATION}


# === AI Reasoning ===

The answer is 42.


# === AI ===

42.


# === AI Status ===

Status info here.
"""
        self.assertEqual(
            [
                "Model: fake/model2\n",
                "Reasoning: on\n",
                "Streaming: on\n",
                "Temperature: 2.0\n",
                "Waiting for fake...",
                "\n\n# === AI Reasoning ===\n\n",
                "6*9",
                " which is 42",
                " in base 13.",
                "\n\n# === AI ===\n\n",
                "6",
                "*",
                "9",
                ".",
                "\n",
                "\n# === AI Status ===\n\nStatus info here.\n",
            ],
            response_chunks,
        )
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())
        self.assertEqual("model2", ai_client.model)
        self.assertEqual(
            [
                ai_cat.Message(type=ai_cat.MessageType.SYSTEM, text="Custom system prompt."),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="What is a question?"),
                ai_cat.Message(type=ai_cat.MessageType.AI, text="A sentence seeking an answer."),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="And what is The Answer?"),
            ],
            ai_client.conversation,
        )
        self.assertEqual(2.0, ai_client.temperature)
        self.assertEqual(ai_cat.Reasoning.ON, ai_client.reasoning)
        self.assertEqual(True, ai_client.streaming)

    def test_changed_settings_are_appended_to_the_conversation(self):
        ai_messenger, ai_client, response_chunks = self.ask(
            self.LONG_CONVERSATION,
            [
                [
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=False, text="42."),
                ],
            ],
        )

        ai_messenger.set_model("fake/model1")
        conv_1 = ai_messenger.conversation_to_str()

        ai_messenger.set_reasoning(ai_cat.Reasoning.OFF.value)
        conv_2 = ai_messenger.conversation_to_str()

        ai_messenger.set_streaming(ai_cat.Streaming.OFF.value)
        conv_3 = ai_messenger.conversation_to_str()

        ai_messenger.set_temperature(0.0)
        conv_4 = ai_messenger.conversation_to_str()

        expected_conversation = (
            self.NOTES
            + "\n\n"
            + self.LONG_CONVERSATION
            + "\n\n\n# === AI ===\n\n42.\n\n\n"
        )

        expected_settings_1 = """\
# === Settings ===

Model: fake/model1
Reasoning: on
Streaming: on
Temperature: 2.0

"""

        expected_settings_2 = """\
# === Settings ===

Model: fake/model1
Reasoning: off
Streaming: on
Temperature: 2.0

"""

        expected_settings_3 = """\
# === Settings ===

Model: fake/model1
Reasoning: off
Streaming: off
Temperature: 2.0

"""

        expected_settings_4 = """\
# === Settings ===

Model: fake/model1
Reasoning: off
Streaming: off
Temperature: 0.0

"""

        self.assertEqual(expected_conversation + expected_settings_1, conv_1)
        self.assertEqual(expected_conversation + expected_settings_2, conv_2)
        self.assertEqual(expected_conversation + expected_settings_3, conv_3)
        self.assertEqual(expected_conversation + expected_settings_4, conv_4)

    def test_parsing_keeps_blocks_boundaries_as_they_were_supplied_except_for_multiple_system_prompts(self):
        conversation = """\
# === System ===

System 2


# === Settings ===

Model: fake/model1


# === Settings ===

Model: fake/model2


# === User ===

User 1


# === User ===

User 2


# === AI Reasoning ===

Reasoning 1


# === AI Reasoning ===

Reasoning 2


# === AI ===

AI 1


# === AI ===

AI 2


# === AI Status ===

Status 1


# === AI Status ===

Status 2


# === User ===

User 3
"""
        edited_conversation = f"""
# === System ===

System 1


# === Notes ===

Note 1


# === Notes ===

Note 2


{conversation}\
"""

        ai_messenger, ai_client, response_chunks = self.ask(
            conversation,
            [
                [
                    ai_cat.AiResponse(is_delta=False, is_reasoning=False, is_status=False, text="AI 3"),
                ],
            ],
        )

        expected_conversation = self.NOTES + "\n\n" + conversation + """

# === AI ===

AI 3
"""

        self.assertEqual("model2", ai_client.model)
        self.assertEqual(
            [
                ai_cat.Message(type=ai_cat.MessageType.SYSTEM, text="System 2"),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="User 1"),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="User 2"),
                ai_cat.Message(type=ai_cat.MessageType.AI, text="AI 1"),
                ai_cat.Message(type=ai_cat.MessageType.AI, text="AI 2"),
                ai_cat.Message(type=ai_cat.MessageType.USER, text="User 3"),
            ],
            ai_client.conversation,
        )
        self.assertEqual(expected_conversation, ai_messenger.conversation_to_str())


class FakeAiClient(ai_cat.AiClient):
    def __init__(
            self,
            responses: collections.abc.Sequence[collections.abc.Sequence[ai_cat.AiResponse]],
    ):
        self.responses = responses
        self.model = None
        self.conversation = None
        self.temperature = None
        self.reasoning = None
        self.streaming = None

    def list_models(self) -> collections.abc.Sequence[str]:
        return ["model1", "model2"]

    def respond(
            self,
            model: str,
            conversation: typing.Iterator[ai_cat.Message],
            temperature: float,
            reasoning: ai_cat.Reasoning,
    ) -> typing.Iterator[ai_cat.AiResponse]:
        yield from self._respond(
            model,
            conversation,
            temperature,
            reasoning,
            streaming=False,
        )

    def respond_streaming(
            self,
            model: str,
            conversation: typing.Iterator[ai_cat.Message],
            temperature: float,
            reasoning: ai_cat.Reasoning,
    ) -> typing.Iterator[ai_cat.AiResponse]:
        yield from self._respond(
            model,
            conversation,
            temperature,
            reasoning,
            streaming=True,
        )

    def _respond(
            self,
            model: str,
            conversation: typing.Iterator[ai_cat.Message],
            temperature: float,
            reasoning: ai_cat.Reasoning,
            streaming: bool,
    ) -> typing.Iterator[ai_cat.AiResponse]:
        self.model = model
        self.conversation = conversation
        self.temperature = temperature
        self.reasoning = reasoning
        self.streaming = streaming

        response = self.responses.pop(0)

        yield from response


class TestableWrappingPrinter(ai_cat.WrappingPrinter):
    def __init__(self):
        super().__init__()

        self.printed = ""

    def _print_impl(self, text, end=os.linesep, file=sys.stdout, flush=False):
        self.printed += text + end


class TestWrappingPrinter(unittest.TestCase):
    def test_basic_wrapping(self):
        printer = TestableWrappingPrinter()
        printer.set_width(20)
        printer.print("The quick brown fox jumps over the lazy dog.", end="\n")
        printer.print("", end="\n")
        printer.print("This is a long long long long long long line.\n", end="")
        printer.print("```\nThis is a long long long conde line.\n```\n", end="")
        printer.print("This is a ", end="")

        for i in range(10):
            printer.print("long ", end="")

        printer.print("line.\n", end="")
        printer.print("\n\n", end="")
        printer.print("a b c d e f g h i j k l m n o p q r s t u v w x y z\n", end="")
        printer.print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n", end="")
        printer.print("---------------------------------------------------\n", end="")

        expected_printed = """\
The quick brown fox 
jumps over the lazy 
dog.

This is a long long 
long long long long 
line.
```
This is a long long long conde line.
```
This is a long long 
long long long long 
long long long long 
line.


a b c d e f g h i j 
k l m n o p q r s t 
u v w x y z
aaaaaaaaaaaaaaaaaaaa
aaaaaaaaaaaaaaaaaaaa
aaaaaaaaaaa
--------------------
--------------------
-----------
"""

        self.assertEqual(expected_printed, printer.printed)


if __name__ == "__main__":
    unittest.main(argv=sys.argv[:1])
