import os
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from io import BytesIO
from pytube import YouTube
from moviepy.editor import *

subscription_key = os.environ.get("SPEECH_KEY")
region = os.environ.get("SPEECH_REGION")


def text_to_speech(text, voice_option):
    speech_config = speechsdk.SpeechConfig(
        subscription=subscription_key,
        region=region,
    )
    speech_config.speech_synthesis_voice_name = voice_option
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
    )

    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=None
    )

    return speech_synthesizer.speak_text_async(text).get()


def speech_to_text(voice_language):
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_recognition_language = voice_language
    audio_config = speechsdk.audio.AudioConfig(filename="audio.wav")

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config
    )
    result = recognizer.recognize_once()
    return result.text


def display_speech_synthesis_result(result):
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        st.info("完了しました")
        audio_data = BytesIO(result.audio_data)
        st.audio(audio_data)
        st.download_button(
            label="ダウンロード",
            data=audio_data,
            file_name="text-to-speech.mp3",
            mime="audio/mpeg",
        )
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        st.error(f"音声合成に失敗しました：{cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                st.error("APIのキーとリージョンが正しいか確認してください")


def download_audio_from_youtube(url):
    yt = YouTube(url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_file = audio_stream.download(filename="audio.mp4")
    audioclip = AudioFileClip(audio_file)
    audioclip.write_audiofile("audio.wav", codec="pcm_s16le")
    os.remove("audio.mp4")


st.title("Azure Cognitive Services App")
tab1, tab2 = st.tabs(["Text to Speech", "Speech to Text"])

with tab1:
    voice_name_jp = ["Ja-Jp-Nanamineural", "ja-JP-KeitaNeural"]
    voice_option = st.radio("音声を選択", voice_name_jp)
    input_option = st.radio("入力方法", ["直接入力する", "テキストファイルを読み込む"])

    text = ""
    if input_option == "直接入力する":
        text = st.text_area("こちらにテキストを入力してください：", "Azure Text-to-Speech用のサンプル文です")
    else:
        uploaded_file = st.file_uploader("テキストファイルをアップロードしてください：", type=["txt"])
        if uploaded_file:
            text = uploaded_file.read().decode("utf-8")

    if st.button("音声を生成"):
        with st.spinner("しばらくお待ちください..."):
            if text:
                result = text_to_speech(text, voice_option)
                display_speech_synthesis_result(result)
            else:
                st.error("テキストを入力してください")

with tab2:
    video_url = st.text_input("YoutubeのURLを入力してEnterを押してください:")
    if video_url:
        st.video(video_url)

        voice_language = st.radio("言語を選択", ["ja-JP", "en-US"])
        if st.button("テキストを生成"):
            with st.spinner("しばらくお待ちください..."):
                download_audio_from_youtube(video_url)
                text = speech_to_text(voice_language)
                st.info(text)
