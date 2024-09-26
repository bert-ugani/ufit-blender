from .....base.src.operators.core.OT_base import OTBase
from .....base.src.operators.core.prepare import mirror, save_rotation, rotate_part_of_model


class OTMirror(OTBase):
    @classmethod
    def poll(cls, context):
        # check if the uFit object is active
        active_object = context.active_object
        if active_object.select_get() \
                and active_object.type == 'MESH' \
                and active_object.mode == 'OBJECT' \
                and active_object.name == 'uFit':
            return True

    def main_func(self, context):
        mirror(context)

class OTRotatePartModel(OTBase):
    @classmethod
    def poll(cls, context):
        # check if the uFit object is active
        active_object = context.active_object
        if active_object.select_get() \
                and active_object.type == 'MESH' \
                and active_object.mode == 'OBJECT' \
                and active_object.name == 'uFit':
            return True

    def main_func(self, context):
        rotate_part_of_model(context)

class OTSaveRotation(OTBase):
    @classmethod
    def poll(cls, context):
        # check if the uFit object is active
        active_object = context.active_object
        if active_object is not None \
                and active_object.type == 'MESH' \
                and active_object.mode == 'OBJECT' \
                and active_object.name == 'uFit':
            return True

    def main_func(self, context):
        save_rotation(context)
