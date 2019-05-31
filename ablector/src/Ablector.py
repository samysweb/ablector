from pyboolector import Boolector
from pyboolector import BTOR_OPT_INCREMENTAL, BTOR_OPT_MODEL_GEN

class Ablector(Boolector):
    def __init__(self):
        super().__init__()
        self.Set_opt(BTOR_OPT_INCREMENTAL,1)
        self.Set_opt(BTOR_OPT_MODEL_GEN,2)