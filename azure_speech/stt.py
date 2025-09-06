import azure.cognitiveservices.speech as speechsdk
import configs
import logging


logger = logging.getLogger("AgentSystem")


def speech_to_text_once():
    """
    通过麦克风实时获取语音
    """
    speech_config = speechsdk.SpeechConfig(subscription=configs.AZURE_SPEECH_CONFIGS.AZURE_SPEECH_KEY, region=configs.AZURE_SPEECH_CONFIGS.AZURE_SPEECH_REGION)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, language="zh-CN")

    result = speech_recognizer.recognize_once_async().get()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        logger.info("[SPEECH] 识别到的文本: {}".format(result.text))
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        logger.info("[SPEECH] 未识别到语音")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        logger.info("[SPEECH] 识别取消: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            logger.info("[SPEECH] 错误详情: {}".format(cancellation_details.error_details))
    return None
