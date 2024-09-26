# prep functions
from ...base.src.operators.core.prepare import (
    prep_move_scan, prep_clean_up, prep_verify_clean_up, prep_rotate)
from ...base.src.operators.core.sculpt import (
    prep_push_pull_smooth, minimal_prep_push_pull_smooth, prep_draw, prep_cutout, minimal_prep_new_cutout, prep_cutout_prep,
    prep_cutout_selection, prep_scaling, prep_verify_scaling, minimal_prep_free_sculpt)
from ...base.src.operators.core.finish import prep_export

# conditions
from ...base.src.properties import conditions


fs_path_consts = {
    'name': 'Free_sculpting',
    'paths': {
        'images_path': '/free_sculpting/static/images',
        'assistance_path': '/free_sculpting/static/images/assistance',
        'workflow_path': '/free_sculpting/src/workflow'
    },
}

fs_ui_consts = {
    'persistent': {},
    'modal': {},
    # keys of workflow must be in the correct order!
    'workflow': {
        'start': {
            'ui_name': 'Start Free Modeling'},
        'import_scan': {
            'ui_name': 'Import Scan'},
        'indicate': {
            'ui_name': 'Indicate',
            'help_text': 'Indicate a relevant point that will be used for alignment in the next steps.'},
        'clean_up': {
            'ui_name': 'Clean Up',
            'help_text': 'Hold Left-Click and move mouse to select the relevant area of the scan. '
                         'Hold SHIFT to add more selected area. Hold CTRL to remove selected area.'},
        'verify_clean_up': {
            'ui_name': 'Verify Clean Up',
            'help_text': 'Verify the clean up is what you expected. The potential issues are highlighted.'},
        'rotate': {
            'ui_name': 'Rotate',
            'help_text': 'Use the rotation tool to align the scan. Make sure it faces directly '
                         'towards you from the front view.'},
        'push_pull_smooth': {
            'ui_name': 'Sculpt',
            'help_text': 'For guided sculpting, hold Left-Click and move mouse to highlight an area. '
                         'Use CTRL-Click to remove highlighted area. '
                         'Once the area is highlighted, use the options in the menu to perform an action'},
        'scale': {
            'ui_name': 'Scaling',
            'help_text': 'Scale the scan in mm or % to increase or decrease its size.'},
        'verify_scaling': {
            'ui_name': 'Verify Scaling',
            'help_text': 'Verify the scaling is what you expected.'},
        'border_choice': {
            'ui_name': 'Borders',
            'help_text': 'Would you like to set border on the model?'},
        'cutout_prep': {
            'ui_name': 'Prepare Border',
            'help_text': 'Indicate the border by adding many points. '
                         'Deselect a point by clicking it again while holding CTRL.'},
        'cutout': {
            'ui_name': 'Border Corrections',
            'technical_name': 'cutout',
            'help_text': 'Make corrections to the border curve by selecting a point using Left-Click, '
                         'press G, move mouse to the destination and Left-Click again.'},
        'cutout_selection': {
            'ui_name': 'Part Selection',
            'technical_name': 'cutout_selection',
            'help_text': 'Select the part you would like to keep.'},
        'new_cutout': {
            'ui_name': 'Another Border or Continue?',
            'technical_name': 'new_cutout',
            'help_text': 'Click the button Another Border if you would another border. '
                         'Click Next to continue to the next step.'},
        'draw': {
            'ui_name': 'Draw Model',
            'help_text': 'Draw the shape of the model by holding down the left mouse button and moving the brush '
                         'over the scan. Use CTRL-Click to remove drawn area.'},
        'export': {
            'ui_name': 'Export Model',
            'help_text': 'Verify the results before exporting the model.'},
        'finish': {
            'ui_name': 'Finished'},
    },
}

fs_operator_consts = {
    'start_modeling': {
        'checkpoint': None,
        'next_step': {
            'name': 'import_scan',
            'default_state': None,
            'reset_substep': True,
            'prep_func': None,
            'exec_save': False
        },
    },
    'start_from_existing': {
        'checkpoint': None,
        'next_step': None,
    },
    'import_scan': {
        'checkpoint': None,
        'next_step': {
            'name': 'indicate',
            'default_state': {
                'object_name': 'uFit',
                'light': 'FLAT',
                'color_type': 'TEXTURE'
            },
            'reset_substep': True,
            'prep_func': prep_move_scan,
            'exec_save': True
        },

    },
    'move_scan': {
        'checkpoint': {
            'name': 'indicate',
            'sub_steps': False
        },
        'next_step': {
            'name': 'clean_up',
            'default_state': {
                'object_name': 'uFit',
                'light': 'FLAT',
                'color_type': 'TEXTURE'
            },
            'reset_substep': True,
            'prep_func': prep_clean_up,
            'exec_save': True
        },
    },
    'clean_up': {
        'checkpoint': {
            'name': 'clean_up',
            'sub_steps': False
        },
        'next_step': {
            'name': 'verify_clean_up',
            'default_state': {
                'object_name': 'uFit',
                'light': 'FLAT',
                'color_type': 'TEXTURE'
            },
            'reset_substep': True,
            'prep_func': prep_verify_clean_up,
            'exec_save': True
        },
    },
    'highlight_non_manifold': {
        'checkpoint': None,
        'next_step': None,
    },
    'fill_non_manifold': {
        'checkpoint': {
            'name': 'verify_clean_up',
            'sub_steps': True
        },
        'next_step': {
            'name': 'verify_clean_up',
            'default_state': None,
            'reset_substep': False,
            'prep_func': None,
            'exec_save': True
        },
    },
    'delete_non_manifold': {
        'checkpoint': {
            'name': 'verify_clean_up',
            'sub_steps': True
        },
        'next_step': {
            'name': 'verify_clean_up',
            'default_state': None,
            'reset_substep': False,
            'prep_func': None,
            'exec_save': True
        },
    },
    'verify_clean_up': {
        'checkpoint': {
            'name': 'verify_clean_up',
            'sub_steps': False
        },
        'next_step': {
            'name': 'rotate',
            'default_state': {
                'object_name': 'uFit',
                'light': 'FLAT',
                'color_type': 'VERTEX',
                'overlay_axes': (1, 1, 1),
                'overlay_text': True,
                'quad_view': True,
                'ortho_view': True,
                'pivot_point': 'CURSOR',
                'orientation_type': 'GLOBAL',
            },
            'reset_substep': True,
            'prep_func': prep_rotate,
            'exec_save': True
        },
    },
    'mirror': {
        'checkpoint': None,
        'next_step': None
    },
    'rotate_part_of_model': {
        'checkpoint': None,
        'next_step': None
    },
    'rotate': {
        'checkpoint': {
            'name': 'rotate',
            'sub_steps': False
        },
        'next_step': {
            'name': 'push_pull_smooth',
            'default_state': {
                'object_name': 'uFit',
                'light': 'FLAT',
                'color_type': 'VERTEX'
            },
            'reset_substep': True,
            'prep_func': prep_push_pull_smooth,
            'exec_save': True,
        },
    },
    'push_pull_region': {
        'checkpoint': {
            'name': 'push_pull_smooth',
            'sub_steps': True
        },
        'next_step': {
            'name': 'push_pull_smooth',
            'default_state': None,
            'reset_substep': False,
            'prep_func': minimal_prep_push_pull_smooth,
            'exec_save': True
        },
    },
    'smooth_region': {
        'checkpoint': {
            'name': 'push_pull_smooth',
            'sub_steps': True
        },
        'next_step': {
            'name': 'push_pull_smooth',
            'default_state': None,
            'reset_substep': False,
            'prep_func': minimal_prep_push_pull_smooth,
            'exec_save': True
        },
    },
    'free_sculpt_checkpoint': {
        'checkpoint': {
            'name': 'push_pull_smooth',
            'sub_steps': True
        },
        'next_step': {
            'name': 'push_pull_smooth',
            'default_state': None,
            'reset_substep': False,
            'prep_func': minimal_prep_free_sculpt,
            'exec_save': True
        },
    },
    'push_pull_smooth_done': {
        'checkpoint': None,
        'next_step': {
            'name': 'scale',
            'default_state': {
                'object_name': 'uFit',
                'light': 'STUDIO',
                'color_type': 'VERTEX'
            },
            'reset_substep': True,
            'prep_func': prep_scaling,
            'exec_save': True
        },
    },
    'scale': {
        'checkpoint': {
            'name': 'scale',
            'sub_steps': False
        },
        # 'next_step': None,  # replaced by custom main_func
        'next_step': {
            'conditions': [
                {
                    'condition_func': conditions.scale_condition,
                    'name': 'verify_scaling',
                    'default_state': {
                        'object_name': 'uFit',
                        'light': 'STUDIO',
                        'color_type': 'RANDOM'
                    },
                    'reset_substep': True,
                    'prep_func': None,
                    'exec_save': True
                },
                {
                    'condition_func': conditions.no_scale_condition,
                    'name': 'border_choice',
                    'default_state': {
                        'object_name': 'uFit',
                        'light': 'STUDIO',
                        'color_type': 'MATERIAL'
                    },
                    'reset_substep': True,
                    'prep_func': None,
                    'exec_save': True
                }
            ]
        }
    },
    'verify_scaling': {
        'checkpoint': {
            'name': 'verify_scaling',
            'sub_steps': False
        },
        'next_step': {
            'name': 'border_choice',
            'default_state': {
                'object_name': 'uFit',
                'light': 'FLAT',
                'color_type': 'VERTEX'
            },
            'reset_substep': True,
            'prep_func': None,
            'exec_save': True
        },
    },
    'border_choice': {
        'checkpoint': {
            'name': 'border_choice',
            'sub_steps': False
        },
        'next_step': {
            'conditions': [
                {
                    'condition_func': conditions.border_condition,
                    'name': 'cutout_prep',
                    'default_state': {
                        'object_name': 'uFit',
                        'light': 'FLAT',
                        'color_type': 'VERTEX'
                    },
                    'reset_substep': True,
                    'prep_func': prep_cutout_prep,
                    'exec_save': True
                },
{
                    'condition_func': conditions.no_border_condition,
                    'name': 'draw',
                    'default_state': {
                        'object_name': 'uFit',
                        'light': 'STUDIO',
                        'color_type': 'MATERIAL'
                    },
                    'reset_substep': True,
                    'prep_func': prep_draw,
                    'exec_save': True
                }
            ]
        },
    },
    'cutout_prep': {
        'checkpoint': {
            'name': 'cutout_prep',
            'sub_steps': True
        },
        # 'next_step': None,
        'next_step': {
            'conditions': [
                {
                    'condition_func': conditions.cutout_style_free_condition,
                    'name': 'cutout',
                    'default_state': {
                        'object_name': 'uFit',
                        'light': 'FLAT',
                        'color_type': 'VERTEX'
                    },
                    'reset_substep': False,
                    'prep_func': prep_cutout,
                    'exec_save': True
                },
                {
                    'condition_func': conditions.cutout_style_straight_condition,
                    'name': 'cutout_selection',
                    'default_state': {
                        'object_name': 'uFit_part1',
                        'light': 'STUDIO',
                        'color_type': 'VERTEX',
                        'focus': False
                    },
                    'reset_substep': False,
                    'prep_func': prep_cutout_selection,
                    'exec_save': True
                }
            ]
        },
    },
    'cutout': {
        'checkpoint': {
            'name': 'cutout',
            'sub_steps': True
        },
        # 'next_step': None,
        'next_step': {
            'name': 'cutout_selection',
            'default_state': {
                'object_name': 'uFit_part1',
                'light': 'STUDIO',
                'color_type': 'VERTEX',
                'focus': False
            },
            'reset_substep': False,
            'prep_func': prep_cutout_selection,
            'exec_save': True
        },
    },
    'cutout_selection': {
        'checkpoint': {
            'name': 'cutout_selection',
            'sub_steps': False
        },
        'next_step': {
            'name': 'new_cutout',
            'default_state': {
                'object_name': 'uFit',
                'light': 'STUDIO',
                'color_type': 'VERTEX'
            },
            'reset_substep': False,
            'prep_func': None,
            'exec_save': True
        },
    },
    'new_cutout': {
        'checkpoint': {
            'name': 'new_cutout',
            'sub_steps': True
        },
        'next_step': {
            'name': 'cutout_prep',
            'default_state': {
                'object_name': 'uFit',
                'light': 'FLAT',
                'color_type': 'VERTEX'
            },
            'reset_substep': False,
            'prep_func': minimal_prep_new_cutout,
            'exec_save': True
        },
    },
    'cutout_done': {
        'checkpoint': {
            'name': 'new_cutout',
            'sub_steps': True
        },
        'next_step': {
            'name': 'draw',
            'default_state': {
                'object_name': 'uFit',
                'light': 'STUDIO',
                'color_type': 'MATERIAL'
            },
            'reset_substep': True,
            'prep_func': prep_draw,
            'exec_save': True
        },
    },
    'apply_draw': {
        'checkpoint': {
            'name': 'draw',
            'sub_steps': False
        },
        # 'next_step': None,
        'next_step': {
            'name': 'export',
            'default_state': {
                'object_name': 'uFit',
                'light': 'STUDIO',
                'color_type': 'RANDOM'
            },
            'reset_substep': True,
            'prep_func': prep_export,
            'exec_save': True
        },
    },
    'export': {
        'checkpoint': {
            'name': 'export',
            'sub_steps': False
        },
        'next_step': {
            'name': 'finish',
            'default_state': {
                'object_name': 'uFit',
                'light': 'STUDIO',
                'color_type': 'RANDOM'
            },
            'reset_substep': True,
            'prep_func': None,
            'exec_save': True
        },
    },
    'restart': {
        'checkpoint': None,
        'next_step': {
            'name': 'start',
            'default_state': None,
            'reset_substep': True,
            'prep_func': None,
            'exec_save': False
        },
    },
}
