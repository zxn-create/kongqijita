import os
import json
import math
import time
from pathlib import Path
from typing import Any, Iterable, List, Sequence, Tuple, Union

try:
	import yaml
except Exception:  # pragma: no cover - optional dependency
	yaml = None

try:
	import numpy as np
except Exception:  # pragma: no cover - numpy should normally be installed
	np = None

try:
	import soundfile as sf
except Exception:  # pragma: no cover - optional fallback
	sf = None

__all__ = [
	"load_config",
	"calculate_distance",
	"normalize_coordinates",
	"create_rotation_matrix",
	"interpolate_color",
	"ensure_directory",
	"load_audio_file",
	"FPSController",
]


def load_config(path: Union[str, Path, None] = None) -> dict:
	"""Load config from YAML or JSON file.

	If `path` is None, this will look for a config file in the project root in the
	following order: environment variable `CONFIG_PATH`, `config.yaml`, `config.yml`,
	`config.json`. Returns empty dict on failure.
	"""
	# Allow override from environment
	env_path = os.environ.get("CONFIG_PATH")
	if env_path:
		p = Path(env_path)
	else:
		if path is None:
			root = Path(__file__).parent
			candidates = [root / "config.yaml", root / "config.yml", root / "config.json"]
			p = next((c for c in candidates if c.exists()), None)
		else:
			p = Path(path)

	if p is None or not Path(p).exists():
		return {}

	try:
		text = Path(p).read_text(encoding="utf-8")
	except Exception:
		return {}

	# Try YAML first (it's a superset of JSON)
	if yaml is not None:
		try:
			return yaml.safe_load(text) or {}
		except Exception:
			pass
	try:
		return json.loads(text)
	except Exception:
		return {}


def calculate_distance(a: Iterable[float], b: Iterable[float]) -> float:
	"""Euclidean distance between two points (2D/3D/... iterable)."""
	if np is not None:
		return float(np.linalg.norm(np.array(a) - np.array(b)))
	# fallback
	a_list = list(a)
	b_list = list(b)
	return math.sqrt(sum((x - y) ** 2 for x, y in zip(a_list, b_list)))


def normalize_coordinates(
	coords: Union[Sequence[float], Sequence[Sequence[float]]], width: float, height: float, to_center: bool = False
) -> Union[Tuple[float, float], List[Tuple[float, float]]]:
	"""
	Normalize coordinates from pixel space to [0,1] (or [-1,1] if to_center=True).
	Accepts single (x, y) or iterable of points.
	"""
	def _norm(pt):
		x, y = float(pt[0]), float(pt[1])
		nx = x / float(width) if width else 0.0
		ny = y / float(height) if height else 0.0
		if to_center:
			nx = nx * 2.0 - 1.0
			ny = ny * 2.0 - 1.0
		return (nx, ny)

	# detect single point
	if isinstance(coords[0], (int, float)):
		return _norm(coords)  # type: ignore[index]
	return [_norm(pt) for pt in coords]  # type: ignore[arg-type]


def create_rotation_matrix(axis: Union[str, Sequence[float]], angle: float):
	"""Create a 3x3 rotation matrix.

	axis can be 'x','y','z' or a 3-element sequence for arbitrary axis.
	Angle is in radians.
	Returns a numpy array if numpy is available, otherwise a nested list.
	"""
	c = math.cos(angle)
	s = math.sin(angle)

	if isinstance(axis, str):
		ax = axis.lower()
		if ax == "x":
			mat = [[1, 0, 0], [0, c, -s], [0, s, c]]
		elif ax == "y":
			mat = [[c, 0, s], [0, 1, 0], [-s, 0, c]]
		else:
			mat = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
	else:
		# arbitrary axis using Rodrigues' rotation formula
		ax = list(axis)
		lx = float(ax[0])
		ly = float(ax[1])
		lz = float(ax[2])
		norm = math.sqrt(lx * lx + ly * ly + lz * lz) or 1.0
		lx /= norm
		ly /= norm
		lz /= norm
		mat = [
			[c + lx * lx * (1 - c), lx * ly * (1 - c) - lz * s, lx * lz * (1 - c) + ly * s],
			[ly * lx * (1 - c) + lz * s, c + ly * ly * (1 - c), ly * lz * (1 - c) - lx * s],
			[lz * lx * (1 - c) - ly * s, lz * ly * (1 - c) + lx * s, c + lz * lz * (1 - c)],
		]

	if np is not None:
		return np.array(mat, dtype=float)
	return mat


def interpolate_color(c1: Sequence[int], c2: Sequence[int], t: float) -> Tuple[int, ...]:
	"""Linearly interpolate between two colors. Colors are sequences of 3 or 4 ints (0-255)."""
	t = max(0.0, min(1.0, float(t)))
	out = []
	for a, b in zip(c1, c2):
		out.append(int(round((1 - t) * a + t * b)))
	return tuple(out)


def ensure_directory(path: Union[str, Path]) -> Path:
	p = Path(path)
	p.mkdir(parents=True, exist_ok=True)
	return p


def load_audio_file(path: Union[str, Path], target_sr: int | None = None) -> Tuple[Any, int]:
	"""
	Load an audio file. Returns (data, sample_rate).
	If `soundfile` is available it will be used; otherwise a simple wave fallback is attempted.
	The returned data is a numpy array when numpy and soundfile are available.
	"""
	p = Path(path)
	if not p.exists():
		raise FileNotFoundError(f"Audio file not found: {p}")

	if sf is not None and np is not None:
		data, sr = sf.read(str(p), always_2d=False)
		if target_sr is not None and sr != target_sr:
			# simple resample using numpy (nearest-neighbor) if needed
			ratio = float(target_sr) / float(sr)
			new_len = int(round(len(data) * ratio))
			data = np.interp(np.linspace(0, len(data) - 1, new_len), np.arange(len(data)), data).astype(data.dtype)
			sr = target_sr
		return data, sr

	# fallback using wave (only supports PCM WAV)
	import wave
	import struct

	with wave.open(str(p), "rb") as wf:
		sr = wf.getframerate()
		nchan = wf.getnchannels()
		sampwidth = wf.getsampwidth()
		nframes = wf.getnframes()
		raw = wf.readframes(nframes)
		fmt = {1: "b", 2: "h", 4: "i"}.get(sampwidth, "h")
		total = nframes * nchan
		vals = struct.unpack("<" + fmt * total, raw)
		if np is not None:
			arr = np.array(vals, dtype=float)
			if nchan > 1:
				arr = arr.reshape(-1, nchan)
			return arr, sr
		return list(vals), sr


class FPSController:
	"""Simple FPS controller to cap frame rate and measure delta time."""

	def __init__(self, target_fps: float = 30.0):
		self.target_fps = float(target_fps) if target_fps and target_fps > 0 else 30.0
		self._last = time.perf_counter()

	def tick(self) -> float:
		"""Waits the necessary time to keep target FPS and returns delta seconds."""
		now = time.perf_counter()
		elapsed = now - self._last
		target_dt = 1.0 / self.target_fps
		to_sleep = max(0.0, target_dt - elapsed)
		if to_sleep:
			time.sleep(to_sleep)
		now2 = time.perf_counter()
		dt = now2 - self._last
		self._last = now2
		return dt

