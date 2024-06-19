import asyncio

async def transcribe_voice(async_client, file_path):
    with open(file_path, "rb") as audio_file:
        transcript = await async_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="json"
        )
    return transcript.text

async def generate_response(async_client, text):
    try:
        assistant = await async_client.beta.assistants.create(
            name="Assistant",
            instructions="Ответь кратко и понятно",
            model="gpt-4-1106-preview"
        )

        thread = await async_client.beta.threads.create()

        await async_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=text
        )

        run = await async_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        while run.status in ["queued", "in_progress"]:
            run = await async_client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            await asyncio.sleep(0.5)

        messages = await async_client.beta.threads.messages.list(thread_id=thread.id)

        assistant_response = None
        for message in messages.data:
            if message.role == 'assistant':
                assistant_response = message.content[0].text.value
                break

        return assistant_response

    except Exception as e:
        print(e)
        return "Failed to generate a response. Please try again later."

async def synthesize_speech(async_client, text, file_path):
    try:
        response = await async_client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )

        new_path = file_path.replace(".ogg", "2.ogg")
        with open(new_path, "wb") as f:
            f.write(response.read())

        return new_path
    except Exception as e:
        print(e)
