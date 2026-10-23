

"""Burst-loss comparison: No ECC, Reed-Solomon, and Fountain."""



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

RESULT_PATH = Path("results/tables/burst_recovery_results.csv")



PACKET_SIZE = 256



DATA_PER_GROUP = 8

PARITY_OPTIONS = [2, 4, 8]



FOUNTAIN_BLOCK_SIZE = 32

FOUNTAIN_OVERHEADS = [1.25, 1.5, 2.0]



LOSS_RATES = [0.05, 0.10, 0.25, 0.50, 0.75]

TRIALS = 30



BAD_TO_GOOD = 0.25





def burst_erase_packets(packets, seed: int, loss_rate: float):

    """Apply a Gilbert-Elliott channel with a target loss rate."""



    if not 0 < loss_rate < 1:

        raise ValueError("loss_rate must be between 0 and 1")



    good_to_bad = (

        loss_rate * BAD_TO_GOOD / (1 - loss_rate)

    )



    rng = random.Random(seed)

    bad_state = False

    received = []



    for packet in packets:

        if bad_state:

            received.append(None)



            if rng.random() < BAD_TO_GOOD:

                bad_state = False

        else:

            received.append(packet)



            if rng.random() < good_to_bad:

                bad_state = True



    return received



def interleave_rs_groups(encoded_groups):

    """Interleave RS packets column-wise across groups."""



    if not encoded_groups:

        return [], []



    transmitted = []

    positions = []



    group_count = len(encoded_groups)

    group_length = len(encoded_groups[0])



    for packet_index in range(group_length):

        for group_index in range(group_count):

            transmitted.append(

                encoded_groups[group_index][packet_index]

            )

            positions.append((group_index, packet_index))



    return transmitted, positions





def deinterleave_rs_packets(received, positions, group_count, group_length):

    """Restore received RS packets to their original groups."""



    restored = [

        [None] * group_length

        for _ in range(group_count)

    ]



    for packet, (group_index, packet_index) in zip(received, positions):

        restored[group_index][packet_index] = packet



    return restored





def run_trial(seed: int, loss_rate: float) -> list[dict]:

    df = pd.read_csv(DATA_PATH)

    source_bytes = serialize(quantize(df))

    source_packets, _ = make_fixed_packets(source_bytes, PACKET_SIZE)

    groups = make_groups(source_packets)



    rows = []





    # No ECC baseline: measure channel and decoding separately.

    no_ecc_channel_start = time.perf_counter()

    no_ecc_received = burst_erase_packets(

        source_packets,

        seed=seed,

        loss_rate=loss_rate,

    )

    no_ecc_channel_seconds = time.perf_counter() - no_ecc_channel_start



    no_ecc_decode_start = time.perf_counter()

    baseline = no_ecc(no_ecc_received)

    no_ecc_decoding_seconds = time.perf_counter() - no_ecc_decode_start



    baseline_recovered = sum(

        packet is not None for packet in baseline.recovered

    )

    source_loss_rate = sum(

        packet is None for packet in no_ecc_received

    ) / len(source_packets)



    rows.append({

        "method": "No ECC",

        "seed": seed,

        "source_loss_rate": source_loss_rate,

        "transmission_loss_rate": source_loss_rate,

        "source_packets": len(source_packets),

        "transmitted_packets": len(source_packets),

        "recovered_source_packets": baseline_recovered,

        "source_packet_recovery_rate": (

            baseline_recovered / len(source_packets)

        ),

        "full_source_recovery": (

            baseline_recovered == len(source_packets)

        ),

                "encoding_seconds": 0.0,

        "channel_seconds": no_ecc_channel_seconds,

        "decoding_seconds": no_ecc_decoding_seconds,

        "target_loss_rate": loss_rate,

    })





    # Reed-Solomon: evaluate three redundancy configurations.

    for parity_count in PARITY_OPTIONS:



        rs_encoding_start = time.perf_counter()



        encoded_groups = [

            rs_encode_group(group, parity_count)

            for group in groups

        ]



        parity_groups = [

            encoded[DATA_PER_GROUP:]

            for encoded in encoded_groups

        ]



        rs_encoding_seconds = (

            time.perf_counter() - rs_encoding_start

        )



        parity_stream = [

            packet

            for parity_group in parity_groups

            for packet in parity_group

        ]



        # Non-interleaved transmission:

        # all source packets followed by parity packets.

        rs_stream = source_packets + parity_stream



        rs_channel_start = time.perf_counter()



        rs_received = burst_erase_packets(

            rs_stream,

            seed=seed,

            loss_rate=loss_rate,

        )



        rs_channel_seconds = (

            time.perf_counter() - rs_channel_start

        )



        # Source packets experience the same losses as No ECC.

        assert rs_received[:len(source_packets)] == no_ecc_received, (

            "Paired source-packet loss patterns differ."

        )



        exact_rs = 0

        all_rs = True



        rs_decoding_start = time.perf_counter()



        for group_index, group in enumerate(groups):



            data_offset = group_index * DATA_PER_GROUP



            data_received = rs_received[

                data_offset:data_offset + DATA_PER_GROUP

            ]



            parity_offset = (

                len(source_packets)

                + group_index * parity_count

            )



            parity_received = rs_received[

                parity_offset:parity_offset + parity_count

            ]



            result = rs_decode_group(

                data_received + parity_received,

                data_count=DATA_PER_GROUP,

                parity_count=parity_count,

            )



            real_count = min(

                DATA_PER_GROUP,

                len(source_packets) - data_offset,

            )



            for i in range(real_count):

                if result.recovered[i] == group[i]:

                    exact_rs += 1

                else:

                    all_rs = False



        rs_decoding_seconds = (

            time.perf_counter() - rs_decoding_start

        )



        rows.append({

            "method": f"Reed-Solomon (8+{parity_count})",

            "seed": seed,

            "target_loss_rate": loss_rate,

            "source_loss_rate": source_loss_rate,

            "transmission_loss_rate": (

                sum(packet is None for packet in rs_received)

                / len(rs_received)

            ),

            "source_packets": len(source_packets),

            "transmitted_packets": len(rs_stream),

            "recovered_source_packets": exact_rs,

            "source_packet_recovery_rate": (

                exact_rs / len(source_packets)

            ),

            "full_source_recovery": all_rs,

            "encoding_seconds": rs_encoding_seconds,

            "channel_seconds": rs_channel_seconds,

            "decoding_seconds": rs_decoding_seconds,

        })



        # Interleaved Reed-Solomon experiment.

        interleaving_start = time.perf_counter()



        interleaved_stream, positions = interleave_rs_groups(

            encoded_groups

        )



        interleaving_seconds = (

            time.perf_counter() - interleaving_start

        )



        interleaved_encoding_seconds = (

            rs_encoding_seconds + interleaving_seconds

        )



        # Reuse the exact same erasure positions as non-interleaved RS.

        # Both streams contain the same number of packets.

        assert len(interleaved_stream) == len(rs_received)



        interleaved_received = [

            packet if original_received is not None else None

            for packet, original_received in zip(

                interleaved_stream, rs_received

            )

        ]



        interleaved_decode_start = time.perf_counter()



        restored_groups = deinterleave_rs_packets(

            interleaved_received,

            positions,

            group_count=len(encoded_groups),

            group_length=DATA_PER_GROUP + parity_count,

        )



        exact_interleaved = 0

        all_interleaved = True



        for group_index, group in enumerate(groups):

            result = rs_decode_group(

                restored_groups[group_index],

                data_count=DATA_PER_GROUP,

                parity_count=parity_count,

            )



            offset = group_index * DATA_PER_GROUP

            real_count = min(

                DATA_PER_GROUP,

                len(source_packets) - offset,

            )



            for i in range(real_count):

                if result.recovered[i] == group[i]:

                    exact_interleaved += 1

                else:

                    all_interleaved = False



        interleaved_decoding_seconds = (

            time.perf_counter() - interleaved_decode_start

        )



        rows.append({

            "method": f"Reed-Solomon Interleaved (8+{parity_count})",

            "seed": seed,

            "target_loss_rate": loss_rate,

            "source_loss_rate": float("nan"),

            "transmission_loss_rate": (

                sum(packet is None for packet in interleaved_received)

                / len(interleaved_received)

            ),

            "source_packets": len(source_packets),

            "transmitted_packets": len(interleaved_stream),

            "recovered_source_packets": exact_interleaved,

            "source_packet_recovery_rate": (

                exact_interleaved / len(source_packets)

            ),

            "full_source_recovery": all_interleaved,

            "encoding_seconds": interleaved_encoding_seconds,

            "channel_seconds": rs_channel_seconds,

            "decoding_seconds": interleaved_decoding_seconds,

        })







    # Fountain: encode every block first, then apply one continuous

    # Gilbert-Elliott channel to the complete transmitted symbol stream.

    for overhead in FOUNTAIN_OVERHEADS:

        blocks = [

            source_packets[offset:offset + FOUNTAIN_BLOCK_SIZE]

            for offset in range(0, len(source_packets), FOUNTAIN_BLOCK_SIZE)

        ]



        encoded_blocks = []

        encoding_start = time.perf_counter()



        for block_index, block in enumerate(blocks):

            output_count = max(

                len(block), math.ceil(len(block) * overhead)

            )

            symbols = fountain_encode(

                block,

                output_count=output_count,

                seed=seed + block_index * 1009,

            )

            encoded_blocks.append(symbols)



        encoding_seconds = time.perf_counter() - encoding_start



        # Flatten symbols in block order and apply the channel exactly once.

        flat_symbols = [

            symbol

            for block_symbols in encoded_blocks

            for symbol in block_symbols

        ]



        channel_start = time.perf_counter()

        flat_received = burst_erase_packets(

            flat_symbols,

            seed=seed + 500_009,

            loss_rate=loss_rate,

        )

        channel_seconds = time.perf_counter() - channel_start



        # Restore block boundaries. Erasures remain None so symbol positions

        # and block membership are preserved.

        received_blocks = []

        cursor = 0

        for block_symbols in encoded_blocks:

            block_length = len(block_symbols)

            received_blocks.append(

                flat_received[cursor:cursor + block_length]

            )

            cursor += block_length



        exact = 0

        all_recovered = True

        decoding_start = time.perf_counter()



        for block, received in zip(blocks, received_blocks):

            surviving_symbols = [

                symbol for symbol in received if symbol is not None

            ]

            recovered = fountain_decode(

                surviving_symbols, source_count=len(block)

            )



            for i, original_packet in enumerate(block):

                if recovered[i] == original_packet:

                    exact += 1

                else:

                    all_recovered = False



        decoding_seconds = time.perf_counter() - decoding_start

        total_symbols = len(flat_symbols)

        total_lost_symbols = sum(

            symbol is None for symbol in flat_received

        )



        rows.append({

            "method": f"Fountain ({overhead:.2f}x)",

            "seed": seed,

            "target_loss_rate": loss_rate,

            "source_loss_rate": float("nan"),

            "transmission_loss_rate": (

                total_lost_symbols / total_symbols

            ),

            "source_packets": len(source_packets),

            "transmitted_packets": total_symbols,

            "recovered_source_packets": exact,

            "source_packet_recovery_rate": exact / len(source_packets),

            "full_source_recovery": all_recovered,

            "encoding_seconds": encoding_seconds,

            "channel_seconds": channel_seconds,

            "decoding_seconds": decoding_seconds,

        })





    return rows





def main():

    all_rows = []



    for loss_rate in LOSS_RATES:

        print(f"Running burst-loss experiments: {loss_rate * 100:.0f}%")



        for trial in range(TRIALS):

            all_rows.extend(

                run_trial(

                    seed=42 + trial,

                    loss_rate=loss_rate,

                )

            )



    results = pd.DataFrame(all_rows)

    expected_rows = len(LOSS_RATES) * TRIALS * 10



    assert len(results) == expected_rows, (

        f"Expected {expected_rows} rows, got {len(results)}"

    )



    print(f"\nPASS: Generated {len(results)} experiment records.")

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)

    results.to_csv(RESULT_PATH, index=False)



    summary = (

        results.groupby(["target_loss_rate", "method"])

        .agg(

            mean_source_loss=("source_loss_rate", "mean"),

            mean_transmission_loss=("transmission_loss_rate", "mean"),

            mean_packet_recovery=("source_packet_recovery_rate", "mean"),

            full_recovery_fraction=("full_source_recovery", "mean"),

            mean_transmitted_packets=("transmitted_packets", "mean"),

            mean_encoding_seconds=("encoding_seconds", "mean"),

            mean_channel_seconds=("channel_seconds", "mean"),

            mean_decoding_seconds=("decoding_seconds", "mean"),

        )

        .reset_index()

    )



    print("=== PAIRED BURST-LOSS SUMMARY ===")

    print(summary.to_string(index=False))

    print(f"\nDetailed results saved to: {RESULT_PATH}")





if __name__ == "__main__":

    main()
