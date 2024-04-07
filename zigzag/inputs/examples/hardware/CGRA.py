import os
from zigzag.classes.hardware.architecture.memory_hierarchy import MemoryHierarchy
from zigzag.classes.hardware.architecture.memory_level import MemoryLevel
from zigzag.classes.hardware.architecture.operational_unit import Multiplier
from zigzag.classes.hardware.architecture.operational_array import MultiplierArray
from zigzag.classes.hardware.architecture.memory_instance import MemoryInstance
from zigzag.classes.hardware.architecture.accelerator import Accelerator
from zigzag.classes.hardware.architecture.core import Core


def memory_hierarchy_dut(multiplier_array, visualize=False):
    """Memory hierarchy variables"""
    """ size=#bit, bw=(read bw, write bw), cost=(read word energy, write work energy) """

    ## Tile registers

    tile_register_128B = MemoryInstance(
        name="rf_128B",
        size=8,
        r_bw=8,
        w_bw=8,
        r_cost=0.095,
        w_cost=0.095,
        area=0,
        r_port=1,
        w_port=1,
        rw_port=0,
        latency=1,
    )

    ## Input buffers

    # sram_32KB_512_1r_1w = \
    #     MemoryInstance(name="sram_32KB", size=32768 * 8, r_bw=512, w_bw=512, r_cost=22.9, w_cost=52.01, area=0,
    #                    r_port=1, w_port=1, rw_port=0, latency=1, min_r_granularity=64, min_w_granularity=64)

    scratchpad_buffer_4KB = MemoryInstance(
        name="scratchpad_4KB",
        size=1024 * 8 * 4,
        r_bw=128 * 4,
        w_bw=128 * 4,
        r_cost=26.01 * 4,
        w_cost=23.65 * 4,
        area=0,
        r_port=1,
        w_port=1,
        rw_port=0,
        latency=1,
        min_r_granularity=64,
        min_w_granularity=64,
    )

    #######################################################################################################################

    # Host Memory

    dram = MemoryInstance(
        name="dram",
        size=10000000000,
        r_bw=64,
        w_bw=64,
        r_cost=700,
        w_cost=750,
        area=0,
        r_port=0,
        w_port=0,
        rw_port=1,
        latency=1,
    )

    memory_hierarchy_graph = MemoryHierarchy(operational_array=multiplier_array)

    """
    fh: from high = wr_in_by_high 
    fl: from low = wr_in_by_low 
    th: to high = rd_out_to_high
    tl: to low = rd_out_to_low
    """
    memory_hierarchy_graph.add_memory(
        memory_instance=tile_register_128B,
        operands=("I2",),
        port_alloc=({"fh": "w_port_1", "tl": "r_port_1", "fl": None, "th": None},),
        served_dimensions={(0, 0)},
    )

    ##################################### on-chip highest memory hierarchy initialization #####################################
    
    memory_hierarchy_graph.add_memory(
        memory_instance=scratchpad_buffer_4KB,
        operands=("I1", "I2"),
        port_alloc=(
            {"fh": "w_port_1", "tl": "r_port_1", "fl": None, "th": None},
            {"fh": "w_port_1", "tl": "r_port_1", "fl": None, "th": None},
        ),
        served_dimensions="all",
    )
    
    memory_hierarchy_graph.add_memory(
        memory_instance=scratchpad_buffer_4KB,
        operands=("I1", "I2"),
        port_alloc=(
            {"fh": "w_port_1", "tl": "r_port_1", "fl": None, "th": None},
            {"fh": "w_port_1", "tl": "r_port_1", "fl": None, "th": None},
        ),
        served_dimensions="all",
    )

    memory_hierarchy_graph.add_memory(
        memory_instance=scratchpad_buffer_4KB,
        operands=("I1", "I2"),
        port_alloc=(
            {"fh": "w_port_1", "tl": "r_port_1", "fl": None, "th": None},
            {"fh": "w_port_1", "tl": "r_port_1", "fl": None, "th": None},
        ),
        served_dimensions="all",
    )

    memory_hierarchy_graph.add_memory(
        memory_instance=scratchpad_buffer_4KB,
        operands=("O"),
        port_alloc=(
            {"fh": "w_port_1", "tl": "r_port_1", "fl": "w_port_1", "th": "r_port_1"},
        ),
        served_dimensions="all",
    )
    ####################################################################################################################
    
    memory_hierarchy_graph.add_memory(
        memory_instance=dram,
        operands=("I1", "I2", "O"),
        port_alloc=(
            {"fh": "rw_port_1", "tl": "rw_port_1", "fl": None, "th": None},
            {"fh": "rw_port_1", "tl": "rw_port_1", "fl": None, "th": None},
            {
                "fh": "rw_port_1",
                "tl": "rw_port_1",
                "fl": "rw_port_1",
                "th": "rw_port_1",
            },
        ),
        served_dimensions="all",
    )
    if visualize:
        from zigzag.visualization.graph.memory_hierarchy import (
            visualize_memory_hierarchy_graph,
        )

        visualize_memory_hierarchy_graph(memory_hierarchy_graph)
    return memory_hierarchy_graph


def multiplier_array_dut():
    """Multiplier array variables"""
    multiplier_input_precision = [8, 8]
    multiplier_energy = 0.04
    multiplier_area = 1
    dimensions = {"D1": 4} 

    multiplier = Multiplier(
        multiplier_input_precision, multiplier_energy, multiplier_area
    )
    multiplier_array = MultiplierArray(multiplier, dimensions)

    return multiplier_array


def cores_dut():
    multiplier_array1 = multiplier_array_dut()
    memory_hierarchy1 = memory_hierarchy_dut(multiplier_array1)

    core1 = Core(1, multiplier_array1, memory_hierarchy1)

    return {core1}


cores = cores_dut()
acc_name = os.path.basename(__file__)[:-3]
accelerator = Accelerator(acc_name, cores)
