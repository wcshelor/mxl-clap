from __future__ import annotations

from pathlib import Path

from music21 import meter, metadata, note, stream

from score_embedding_lab.excerpting import (
    build_excerpt_id,
    extract_excerpts_from_file,
    extract_prefix_excerpts_from_directory,
    extract_measure_window,
    iter_measure_windows,
)


def make_tiny_full_score() -> stream.Score:
    score = stream.Score()
    part = stream.Part()
    for measure_number, pitch_name in enumerate(["C4", "D4", "E4", "F4", "G4"], start=1):
        measure = stream.Measure(number=measure_number)
        if measure_number == 1:
            measure.insert(0, meter.TimeSignature("4/4"))
        measure.append(note.Note(pitch_name, quarterLength=4))
        part.append(measure)
    score.append(part)
    score.metadata = metadata.Metadata()
    score.metadata.title = "Tiny Piece"
    score.metadata.composer = "Composer Example"
    return score


def test_iter_measure_windows_uses_contiguous_ranges():
    assert iter_measure_windows(total_measures=5, window_size=2, stride=2) == [(1, 2), (3, 4)]


def test_extract_excerpts_writes_manifest_and_musicxml(tmp_path: Path):
    source_path = tmp_path / "tiny_piece.musicxml"
    output_dir = tmp_path / "excerpts"
    score = make_tiny_full_score()
    score.write("musicxml", fp=str(source_path))

    rows = extract_excerpts_from_file(source_path, output_dir, window_size=2, stride=2)

    assert len(rows) == 2
    assert rows[0]["excerpt_id"] == build_excerpt_id(source_path, 1, 2)
    assert rows[0]["excerpt_file"] == f"{build_excerpt_id(source_path, 1, 2)}.musicxml"
    assert rows[0]["measure_start"] == 1
    assert rows[0]["measure_end"] == 2
    assert rows[0]["source_total_measures"] == 5
    assert rows[0]["title"] == "Tiny Piece"
    assert rows[0]["composer"] == "Composer Example"
    assert (output_dir / rows[0]["excerpt_file"]).exists()
    assert (output_dir / rows[1]["excerpt_file"]).exists()
    excerpt_score = extract_measure_window(score, 1, 2)
    instruments = list(excerpt_score.parts[0].recurse().getElementsByClass("Instrument"))
    assert any(inst.__class__.__name__ == "Piano" for inst in instruments)


def test_extract_prefix_excerpts_writes_first_32_and_64_measures(tmp_path: Path):
    source_path = tmp_path / "tiny_piece.musicxml"
    output_dir = tmp_path / "prefixes"
    score = stream.Score()
    part = stream.Part()
    for measure_number in range(1, 71):
        measure = stream.Measure(number=measure_number)
        measure.append(note.Note("C4", quarterLength=4))
        part.append(measure)
    score.append(part)
    score.write("musicxml", fp=str(source_path))

    frame = extract_prefix_excerpts_from_directory(tmp_path, output_dir, prefix_lengths=[32, 64])

    assert list(frame["measure_end"]) == [32, 64]
    assert list(frame["requested_measure_end"]) == [32, 64]
    assert (output_dir / f"{build_excerpt_id(source_path, 1, 32)}.mxl").exists()
    assert (output_dir / f"{build_excerpt_id(source_path, 1, 64)}.mxl").exists()


def test_extract_prefix_excerpts_keeps_clamped_requests_unique(tmp_path: Path):
    source_path = tmp_path / "tiny_piece.musicxml"
    output_dir = tmp_path / "prefixes"
    score = stream.Score()
    part = stream.Part()
    for measure_number in range(1, 27):
        measure = stream.Measure(number=measure_number)
        measure.append(note.Note("C4", quarterLength=4))
        part.append(measure)
    score.append(part)
    score.write("musicxml", fp=str(source_path))

    frame = extract_prefix_excerpts_from_directory(tmp_path, output_dir, prefix_lengths=[32, 64])

    assert list(frame["measure_end"]) == [26, 26]
    assert list(frame["requested_measure_end"]) == [32, 64]
    assert len(set(frame["excerpt_id"])) == 2
    assert frame.iloc[0]["excerpt_id"].endswith("_req032")
    assert frame.iloc[1]["excerpt_id"].endswith("_req064")
