# -- do not touch
import os

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
# -- end do not touch
import unittest
from datasets import load_dataset  # noqa: E402
from gptqmodel import BACKEND, GPTQModel
from gptqmodel.quantization import FORMAT  # noqa: E402
from gptqmodel.quantization.config import QuantizeConfig # noqa: E402
from transformers import AutoTokenizer  # noqa: E402
import tempfile

class ModelTest(unittest.TestCase):
    GENERATE_EVAL_SIZE = 100

    def generate(self, model, tokenizer, prompt=None):
        if prompt == None:
            prompt = "I am in Paris and"
        device = model.device
        inp = tokenizer(prompt, return_tensors="pt").to(device)
        res = model.generate(**inp, num_beams=1, do_sample=False, min_new_tokens=self.GENERATE_EVAL_SIZE, max_new_tokens=self.GENERATE_EVAL_SIZE)
        output = tokenizer.decode(res[0])

        return output

    def generateChat(self, model, tokenizer, prompt=None):
        if prompt == None:
            prompt = [
                {"role": "system",
                 "content": "You are a helpful assistant."},
                {"role": "user",
                 "content": "I am in Shanghai, preparing to visit the natural history museum. Can you tell me the best way to"}
            ]

        input_tensor = tokenizer.apply_chat_template(prompt, add_generation_prompt=True, return_tensors="pt")
        outputs = model.generate(input_ids=input_tensor.to(model.device), max_new_tokens=self.GENERATE_EVAL_SIZE)
        output = tokenizer.decode(outputs[0][input_tensor.shape[1]:], skip_special_tokens=True)

        return output

    def load_tokenizer(self, model_name_or_path, trust_remote_code=False):
        # print(f"pzs----load_tokenizer {model_name_or_path}---{trust_remote_code}")
        tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=trust_remote_code)
        return tokenizer

    def load_dataset(self, tokenizer):
        traindata = load_dataset("wikitext", "wikitext-2-raw-v1", split="train").filter(lambda x: len(x['text']) >= 512)
        calibration_dataset = [tokenizer(example["text"]) for example in traindata.select(range(1024))]
        return calibration_dataset

    def quantModel(self, model_name_or_path, trust_remote_code=False):
        tokenizer = self.load_tokenizer(model_name_or_path, trust_remote_code=trust_remote_code)
        calibration_dataset = self.load_dataset(tokenizer)
        quantize_config = QuantizeConfig(
            bits=4,
            group_size=128,
            format=FORMAT.GPTQ,
        )
        model = GPTQModel.from_pretrained(
            model_name_or_path,
            quantize_config=quantize_config,
            trust_remote_code=trust_remote_code,
        )

        model.quantize(calibration_dataset, batch_size=64)
        # model.save_quantized("/monster/data/pzs/Qubitium/")
        with tempfile.TemporaryDirectory() as tmpdirname:
            model.save_quantized(tmpdirname)
            q_model, q_tokenizer = self.loadQuantModel(tmpdirname, tokenizer_path=model_name_or_path)

        return q_model, q_tokenizer


    def loadQuantModel(self, model_name_or_path, trust_remote_code=False, tokenizer_path=None):
        if tokenizer_path == None:
            tokenizer_path = model_name_or_path
        else:
            trust_remote_code = True
        tokenizer = self.load_tokenizer(tokenizer_path, trust_remote_code)

        model = GPTQModel.from_quantized(
            model_name_or_path,
            trust_remote_code=trust_remote_code,
        )

        return model, tokenizer