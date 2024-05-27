workload = {
    30: {  # fc
    "operator_type": "Conv",
    "equation": "O[b][k][oy][ox]+=W[k][c][fy][fx]*I[b][c][iy][ix]",
    "dimension_relations": ["ix=1*ox+1*fx", "iy=1*oy+1*fy"],
    "loop_dim_size": {
        "B": 36,
        "K": 36,
        "C": 36,
        "OY": 1,
        "OX": 1,
        "FY": 1,
        "FX": 1,
    },
    "operand_precision": {"O": 16, "O_final": 8, "W": 8, "I": 8},
    "operand_source": {"W": [], "I": []},
    "constant_operands": ["W", "I"],
    }
}
