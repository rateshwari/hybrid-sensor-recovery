"""Unified random packet-loss comparison: No ECC, RS, and Fountain."""



from pathlib import Path

import math

import random

import time



import pandas as pd



from data_pipeline import quantize, serialize

from recovery import no_ecc, rs_encode_group, rs_decode_group

from fountain import encode as fountain_encode, decode as fountain_decode

from experiment import make_fixed_packets, make_groups



DATA_PATH = Path("data/processed/experiment_segment.csv")

RESULT_PATH = Path("results/tables/unified_recovery_results.csv")



PACKET_SIZE = 256

RS_DATA = 8

RS_PARITY_OPTIONS = [2, 4, 8]

FOUNTAIN_BLOCK_SIZE = 32

FOUNTAIN_OVERHEADS = [1.25, 1.5, 2.0]



LOSS_RATES = [0.05, 0.10, 0.25, 0.50, 0.75]



TRIALS = 30





def load_source_packets():

    df = pd.read_csv(DATA_PATH)

    source_bytes = serialize(quantize(df))

    packets, original_length = make_fixed_packets(

        source_bytes, PACKET_SIZE

    )

    return packets, original_length





def drop_packets(packets, probability, seed):

    rng = random.Random(seed)

    return [

        packet if rng.random() >= probability else None

        for packet in packets

    ]





def evaluate_trial(source_packets, loss_rate, seed):

    rows = []



    # Baseline source-packet loss pattern, shared with RS.

    no_ecc_received = drop_packets(source_packets, loss_rate, seed)



    # No ECC

    start = time.perf_counter()

    baseline = no_ecc(no_ecc_received)

    baseline_decode_time = time.perf_counter() - start



    baseline_recovered = sum(

        packet is not None for packet in baseline.recovered

    )



    rows.append({

        "method": "No ECC",

        "loss_rate": loss_rate,

        "seed": seed,

        "source_packets": len(source_packets),

        "transmitted_packets": len(source_packets),

        "exact_recovered_packets": baseline_recovered,

        "exact_recovery_rate": baseline_recovered / len(source_packets),

        "full_source_recovery": baseline_recovered == len(source_packets),

        "encoding_seconds": 0.0,

        "decoding_seconds": baseline_decode_time,

    })



    # Reed-Solomon: evaluate multiple redundancy levels.

    groups = make_groups(source_packets)



    for parity_count in RS_PARITY_OPTIONS:

        encoded_groups = []



        encode_start = time.perf_counter()



        for group in groups:

            encoded_groups.append(

                rs_encode_group(group, parity_count)

            )



        rs_encoding_time = time.perf_counter() - encode_start



        exact_rs = 0

        all_rs_recovered = True



        rs_decode_start = time.perf_counter()



        for group_index, group in enumerate(groups):

            encoded = encoded_groups[group_index]

            offset = group_index * RS_DATA



            # Use exactly the same source-packet losses

            # as the No ECC baseline.

            received_data = no_ecc_received[

                offset:offset + RS_DATA

            ]



            # Reuse the same parity-loss random sequence

            # across RS redundancy configurations.

            parity_rng = random.Random(

                seed + 100_003 + group_index

            )



            received_parity = [

                packet if parity_rng.random() >= loss_rate else None

                for packet in encoded[RS_DATA:]

            ]



            result = rs_decode_group(

                received_data + received_parity,

                data_count=RS_DATA,

                parity_count=parity_count,

            )



            real_count = min(

                RS_DATA,

                len(source_packets) - offset

            )



            for i in range(real_count):

                if result.recovered[i] == group[i]:

                    exact_rs += 1

                else:

                    all_rs_recovered = False



        rs_decoding_time = time.perf_counter() - rs_decode_start



        rows.append({

            "method": f"Reed-Solomon (8+{parity_count})",

            "loss_rate": loss_rate,

            "seed": seed,

            "source_packets": len(source_packets),

            "transmitted_packets": sum(

                len(group) for group in encoded_groups

            ),

            "exact_recovered_packets": exact_rs,

            "exact_recovery_rate": exact_rs / len(source_packets),

            "full_source_recovery": all_rs_recovered,

            "encoding_seconds": rs_encoding_time,

            "decoding_seconds": rs_decoding_time,

        })



    # Fountain coding, independently encoded in blocks.

    for overhead in FOUNTAIN_OVERHEADS:

        exact_fountain = 0

        all_fountain_recovered = True

        total_symbols = 0

        fountain_encoding_time = 0.0

        fountain_decoding_time = 0.0



        for block_index, offset in enumerate(

            range(0, len(source_packets), FOUNTAIN_BLOCK_SIZE)

        ):

            block = source_packets[offset:offset + FOUNTAIN_BLOCK_SIZE]

            count = len(block)

            output_count = max(count, math.ceil(count * overhead))



            encode_start = time.perf_counter()

            symbols = fountain_encode(

                block,

                output_count=output_count,

                seed=seed + block_index * 1009,

            )

            fountain_encoding_time += time.perf_counter() - encode_start

            total_symbols += len(symbols)



            # Encoded symbols have the same loss probability but independent

            # erasure draws; they do not map one-to-one to source packets.



            # Simulate independent packet loss for encoded symbols.

            # Use one deterministic RNG per block.

            rng = random.Random(seed + 500_009 + block_index)

            received_symbols = [

                symbol for symbol in symbols

                if rng.random() >= loss_rate

            ]





            decode_start = time.perf_counter()

            recovered = fountain_decode(received_symbols, source_count=count)

            fountain_decoding_time += time.perf_counter() - decode_start



            for i in range(count):

                if recovered[i] == block[i]:

                    exact_fountain += 1

                else:

                    all_fountain_recovered = False



        rows.append({

            "method": f"Fountain ({overhead:.2f}x)",

            "loss_rate": loss_rate,

            "seed": seed,

            "source_packets": len(source_packets),

            "transmitted_packets": total_symbols,

            "exact_recovered_packets": exact_fountain,

            "exact_recovery_rate": exact_fountain / len(source_packets),

            "full_source_recovery": all_fountain_recovered,

            "encoding_seconds": fountain_encoding_time,

            "decoding_seconds": fountain_decoding_time,

        })



    return rows





def main():

    source_packets, _ = load_source_packets()

    rows = []



    for loss_rate in LOSS_RATES:

        for trial in range(TRIALS):

            seed = 42 + trial

            rows.extend(evaluate_trial(source_packets, loss_rate, seed))



    results = pd.DataFrame(rows)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)

    results.to_csv(RESULT_PATH, index=False)



    summary = (

        results.groupby(["method", "loss_rate"])

        .agg(

            mean_exact_recovery=("exact_recovery_rate", "mean"),

            full_recovery_fraction=("full_source_recovery", "mean"),

            mean_transmitted_packets=("transmitted_packets", "mean"),

            mean_encoding_seconds=("encoding_seconds", "mean"),

            mean_decoding_seconds=("decoding_seconds", "mean"),

        )

        .reset_index()

    )



    print("=== UNIFIED RANDOM-LOSS SUMMARY ===")

    print(summary.to_string(index=False))

    print(f"\nDetailed results saved to: {RESULT_PATH}")





if __name__ == "__main__":

    main()
