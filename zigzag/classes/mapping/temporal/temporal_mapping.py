from typing import Dict
from math import prod
from zigzag.classes.hardware.architecture.accelerator import Accelerator
from zigzag.classes.workload.layer_node import LayerNode
from zigzag.utils import pickle_deepcopy

## Class that collect all the info related to temporal mapping.
class TemporalMapping:

    ## The class constructor
    # @param temporal_mapping_dict
    # @param layer_node
    def __init__(self, temporal_mapping_dict: Dict, layer_node: LayerNode, accelerator):
        self.mapping_dic_origin = temporal_mapping_dict
        self.layer_node = layer_node
        self.operand_list = layer_node.operand_list
        self.accelerator = accelerator

        # Extract memory hierarchy level count for each operand from temporal mapping definition
        self.mem_level = {op: len(tmap) for (op, tmap) in temporal_mapping_dict.items()}

        # For each memory level, if the innermost/bottom loop is ir loop, merge it down to the below level
        self.innermost_stationary_loop_merge_down()

        # Calculate the current and below level (cabl) iteration cycle for each memory level, 
        # i.e., each memory level refreshes once, how many cycles it covers
        self.calc_cycle_cabl_level()

        # Calculate the current and below loop (cabl) iteration cycle for each loop,
        # i.e., each loop iterates once, how many cycles it covers '''
        # self.calc_cycle_cabl_loop()

        # Calculate the top-ir loop size at each memory level, which will be used 
        # to compute instant required memory BW in combined_mapping.py """
        self.calc_top_r_and_ir_loop()

    def __str__(self):
        return str(self.mapping_dic_stationary)

    def __repr__(self):
        return str(self)

    ## JSON representation of this object to save it to a json file.
    def __jsonrepr__(self):
        return {"temporal_mapping": self.mapping_dic_stationary}

    ## Iteratively merging down the ir loops which located at the bottom position of each memory level.
    # Also calculate the MAC level data stationary cycle, i,e., the innermost memory level's bottom ir loops.
    def innermost_stationary_loop_merge_down(self):
        # Initialization
        mapping_current = pickle_deepcopy(self.mapping_dic_origin)
        mapping_previous = pickle_deepcopy(self.mapping_dic_origin)
        systolic_cycles = sum(self.accelerator.get_core(self.layer_node.core_allocation).operational_array.dimension_sizes)-1

        done = False
        empty_level = {op: False for op in self.operand_list}

        while not done:
            mapping_st = {
                op: [[] for _ in range(self.mem_level[op])] for op in self.operand_list
            }
            mapping_st_cycles = {
                op: [[] for _ in range(self.mem_level[op])] for op in self.operand_list
            }
            MAC_level_st = {op: 1 for op in self.operand_list}
            for operand in self.mem_level.keys():
                for level, current_level_loops in enumerate(mapping_previous[operand]):
                    if not current_level_loops:
                        mapping_st[operand][level] = pickle_deepcopy(
                            current_level_loops
                        )
                        mapping_st_cycles[operand][level] = pickle_deepcopy(
                            current_level_loops
                        )
                        empty_level[operand] = True
                    else:
                        for loop_type, loop_dim in current_level_loops:
                            if (
                                loop_type
                                in self.layer_node.operand_loop_dim[operand]["ir"]
                            ):
                                if level == 0:
                                    MAC_level_st[operand] *= loop_dim
                                    mapping_st[operand][level].append(
                                        (loop_type, loop_dim)
                                    )
                                    mapping_st_cycles[operand][level].append(
                                        (loop_type, loop_dim)
                                    )
                                    mapping_current[operand][level].remove(
                                        (loop_type, loop_dim)
                                    )
                                else:
                                    mapping_st[operand][level - 1].append(
                                        (loop_type, loop_dim)
                                    )
                                    mapping_st_cycles[operand][level-1].append(
                                        (loop_type, loop_dim)
                                    )
                                    mapping_current[operand][level].remove(
                                        (loop_type, loop_dim)
                                    )
                            else:
                                mapping_st[operand][level].extend(
                                    mapping_current[operand][level]
                                )
                                mapping_st_cycles[operand][level].extend(
                                    mapping_current[operand][level]
                                )
                                break
                        
                        if level == 0:          #add the systolic cycles to the bottom level stationary cycles, after all the irrelevant loops of the bottom level have been added
                            MAC_level_st[operand] += systolic_cycles       
                            bottom_loop_cycles = mapping_st_cycles[operand][level][0][1]
                            systolic_bottom_loop = (mapping_st_cycles[operand][level][0][0], bottom_loop_cycles + systolic_cycles)
                            mapping_st_cycles[operand][level][0] = systolic_bottom_loop
                        elif empty_level[operand] == True:   #if the bottom memory level(s) for an operand is(/are) unused..
                            if (
                                loop_type
                                in self.layer_node.operand_loop_dim[operand]["ir"]
                            ):
                                bottom_loop_cycles = mapping_st_cycles[operand][level-1][0][1]
                                systolic_bottom_loop = (mapping_st_cycles[operand][level-1][0][0], bottom_loop_cycles + systolic_cycles)
                                mapping_st_cycles[operand][level-1][0] = systolic_bottom_loop
                            else:
                                bottom_loop_cycles = mapping_st_cycles[operand][level][0][1]
                                systolic_bottom_loop = (mapping_st_cycles[operand][level][0][0], bottom_loop_cycles + systolic_cycles)
                                mapping_st_cycles[operand][level][0] = systolic_bottom_loop
                            empty_level[operand] = False

            if mapping_st != mapping_previous:
                mapping_previous = pickle_deepcopy(mapping_st)
                mapping_current = pickle_deepcopy(mapping_st)
                continue
            else:
                done = True

        self.mapping_dic_stationary = mapping_st
        self.mapping_dic_stationary_cycles = mapping_st_cycles
        self.MAC_level_data_stationary_cycle = MAC_level_st

    ## Calculate the iteration cycles that each memory level covers
    def calc_cycle_cabl_level(self):
        # iteration_each_level only counts for the current level for-loops
        iteration_each_level = {
            op: [
                prod(
                    [loop_dim for (_, loop_dim) in self.mapping_dic_stationary_cycles[op][lv]]
                )
                for lv in range(self.mem_level[op])
            ]
            for op in self.operand_list
        }
        # cycle_per_level count for current and below levels' for-loops
        cycle_cabl_level = {
            op: [
                prod(iteration_each_level[op][0 : lv + 1])
                for lv in range(self.mem_level[op])
            ]
            for op in self.operand_list
        }

        # ASSERT: The total cycle count must be the same for all operand
        total_cycle = [cycle_cabl_level[op][-1] for op in self.operand_list]
        assert all(
            x == total_cycle[0] for x in total_cycle
        ), f"The total cycle count is not the same for all operand {total_cycle}, please correct the temporal mapping."

        self.cycle_cabl_level = cycle_cabl_level
        self.total_cycle = total_cycle[0]

    def calc_top_r_and_ir_loop(self):
        # top_ir_loop_size: For each memory level, from top to bottom, the product of top few irrelevant loops.
        # top_ir is used for later required instant memory bandwidth calculation.
    
        # Initialization
        # self.mem_level[op] + 1 to add the placeholder for operational array level
        top_r_loop_size = {
            op: [1 for _ in range(self.mem_level[op] + 1)] for op in self.operand_list
        }

        top_ir_loop_size = {
            op: [1 for _ in range(self.mem_level[op] + 1)] for op in self.operand_list
        }

        # Check and extract the top ir loops
        for operand in self.operand_list:
            for level, current_level_loops in enumerate(
                self.mapping_dic_stationary[operand]
            ):
                if not current_level_loops:
                    continue
                else:
                    for loop_type, loop_dim in reversed(current_level_loops):
                        if loop_type in self.layer_node.operand_loop_dim[operand]["r"]:
                            top_r_loop_size[operand][level + 1] *= loop_dim
                        else:
                            break
                    for loop_type, loop_dim in reversed(current_level_loops):
                        if loop_type in self.layer_node.operand_loop_dim[operand]["ir"]:
                            top_ir_loop_size[operand][level + 1] *= loop_dim
                        else:
                            break

        self.top_r_loop_size = top_r_loop_size
        self.top_ir_loop_size = top_ir_loop_size
