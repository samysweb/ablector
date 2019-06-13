from pysmt.solvers.btor import BoolectorSolver, BTORConverter
from pysmt.decorators import clear_pending_pop

from ablector import Ablector

class AblectorSolver(BoolectorSolver):

    def __init__(self, environment, logic, **options):
        super().__init__(environment,
                            logic,
                            **options)
        self.btor = Ablector()
        self.converter = BTORConverter(environment, self.btor)
        return

    @clear_pending_pop
    def _reset_assertions(self):
        super()._reset_assertions()
        self.btor = Ablector()
        self.converter = BTORConverter(self.environment, self.btor)