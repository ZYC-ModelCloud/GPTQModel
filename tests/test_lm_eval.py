# -- do not touch
import os
# -- end do not touch
import tempfile  # noqa: E402
import unittest  # noqa: E402

from gptqmodel import GPTQModel  # noqa: E402
from lm_eval.utils import make_table

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"

class TestLmEval(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.MODEL_ID = "/monster/data/model/TinyLlama-1.1B-Chat-v1.0-GPTQ-4bit" # "LnL-AI/TinyLlama-1.1B-Chat-v1.0-GPTQ-4bit"

    def test_lm_eval(self):
       with tempfile.TemporaryDirectory() as tmp_dir:
           model = GPTQModel.load(
               self.MODEL_ID
           )
           results = model.lm_eval(
                output_path=tmp_dir,
                tasks='arc_challenge',
            )

           print('--------Eval Result---------')
           print(make_table(results))
           if "groups" in results:
               print(make_table(results, "groups"))
           print('--------Eval Result End---------')

           stored_files = os.listdir(tmp_dir)
           self.assertTrue(len(stored_files) > 0)

