import copy
import json
from importlib.resources import files
import unittest
import numpy as np
from hvideo.config import validate
from hvideo.audio import synthesize, SR
from hvideo.visuals import Renderer
from hvideo.subtitles import timestamp


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.c = json.loads(files("hvideo").joinpath("templates/title-card.json").read_text(encoding="utf-8"))

    def test_scene_relative_audio_matches_absolute(self):
        self.c["audio"]["bed"] = []
        self.c["audio"]["cues"] = [{"scene":"ending","at":.25,"type":"note","frequency":440}]
        relative=validate(self.c)
        absolute=copy.deepcopy(relative)
        absolute["audio"]["cues"][0].pop("scene")
        absolute["audio"]["cues"][0]["at"]=3.25
        a,b=synthesize(relative),synthesize(absolute)
        np.testing.assert_array_equal(a,b)
        self.assertFalse(np.any(a[:round(3.25*SR)]))
        self.assertGreater(np.max(np.abs(a[round(3.25*SR):])),.01)

    def test_duration_seed_and_headroom(self):
        self.c["audio"]["cues"]=[{"type":"sweep","at":1,"duration":2,"gain":2}]
        self.c["audio"]["gain"]=8
        c=validate(self.c)
        first=synthesize(c)
        self.assertEqual(first.shape,(6*SR,2))
        self.assertLessEqual(np.max(np.abs(first)),.920001)
        np.testing.assert_array_equal(first,synthesize(c))
        self.assertFalse(np.any(first[0]))

    def test_reject_invalid_encoding_and_timeline(self):
        for mutate in (
            lambda c:c["video"].update(width=961),
            lambda c:c["scenes"][1].update(start=2),
            lambda c:c["audio"]["cues"][0].update(scene="missing"),
            lambda c:c["audio"].update(gain=float("nan")),
        ):
            c=copy.deepcopy(self.c)
            mutate(c)
            with self.assertRaises(ValueError): validate(c)

    def test_render_is_independent_of_frame_request_order(self):
        c=json.loads(files("hvideo").joinpath("templates/particle-ring.json").read_text(encoding="utf-8"))
        c["video"].update(width=320,height=180)
        renderer=Renderer(validate(c))
        first=np.asarray(renderer.frame(7.5))
        renderer.frame(1)
        np.testing.assert_array_equal(first,np.asarray(renderer.frame(7.5)))
        self.assertEqual(first.shape,(180,320,3))
        self.assertGreater(first.std(),5)

    def test_subtitle_rounding_and_overlap(self):
        self.assertEqual(timestamp(59.9996),"00:01:00,000")
        self.c["subtitles"]=[{"start":0,"end":2,"text":"first"},{"start":1,"end":3,"text":"second"}]
        with self.assertRaises(ValueError): validate(self.c)


if __name__=="__main__": unittest.main()
