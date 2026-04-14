#!/usr/bin/env python3

import argparse
import shlex
from pathlib import Path

from gem5.components.boards.x86_board import X86Board
from gem5.components.cachehierarchies.classic.private_l1_private_l2_walk_cache_hierarchy import (
    PrivateL1PrivateL2WalkCacheHierarchy,
)
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires


CPU_TYPES = {
    "minor": CPUTypes.MINOR,
    "o3": CPUTypes.O3,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a local X86 SE workload in gem5 for coursework experiments."
    )
    parser.add_argument(
        "--cpu",
        required=True,
        choices=sorted(CPU_TYPES),
        help="CPU model to use while keeping all other system parameters fixed.",
    )
    parser.add_argument(
        "--binary",
        required=True,
        help="Path to the local X86 benchmark binary.",
    )
    parser.add_argument(
        "--binary-args",
        default="",
        help="Arguments passed to the benchmark binary as a single shell-style string.",
    )
    parser.add_argument("--clk", default="3GHz", help="Board clock frequency.")
    parser.add_argument(
        "--l1i-size", default="32KiB", help="L1 instruction cache size."
    )
    parser.add_argument(
        "--l1d-size", default="32KiB", help="L1 data cache size."
    )
    parser.add_argument("--l2-size", default="512KiB", help="Private L2 cache size.")
    parser.add_argument(
        "--mem-size",
        default="3GiB",
        help="System memory size. Use 3GiB for X86Board compatibility.",
    )
    parser.add_argument(
        "--max-ticks",
        type=int,
        default=None,
        help="Optional maximum number of ticks before gem5 exits.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    binary_path = Path(args.binary).resolve()

    if not binary_path.is_file():
        raise FileNotFoundError(f"Benchmark binary not found: {binary_path}")

    requires(isa_required=ISA.X86)

    cache_hierarchy = PrivateL1PrivateL2WalkCacheHierarchy(
        l1i_size=args.l1i_size,
        l1d_size=args.l1d_size,
        l2_size=args.l2_size,
    )
    memory = SingleChannelDDR3_1600(size=args.mem_size)
    processor = SimpleProcessor(
        cpu_type=CPU_TYPES[args.cpu],
        isa=ISA.X86,
        num_cores=1,
    )

    board = X86Board(
        clk_freq=args.clk,
        processor=processor,
        memory=memory,
        cache_hierarchy=cache_hierarchy,
    )

    board.set_se_binary_workload(
        BinaryResource(local_path=str(binary_path), architecture=ISA.X86),
        arguments=shlex.split(args.binary_args),
    )

    simulator = Simulator(board=board)
    if args.max_ticks is not None:
        simulator.set_max_ticks(args.max_ticks)

    simulator.run()

    print(
        "Exiting @ tick {} because {}.".format(
            simulator.get_current_tick(),
            simulator.get_last_exit_event_cause(),
        )
    )


if __name__ in ("__main__", "__m5_main__"):
    main()
