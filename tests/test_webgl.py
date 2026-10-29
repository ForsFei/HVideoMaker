"""Opt-in integration tests: HVIDEO_TEST_WEBGL=1 python -m unittest ..."""
import json
import os
from importlib.resources import files
from pathlib import Path
import unittest
import numpy as np
from hvideo.config import validate
from hvideo.webgl import safe_asset


class WebGLConfigTests(unittest.TestCase):
    def test_camera_and_backend_validation(self):
        c=json.loads(files('hvideo').joinpath('templates/cosmic-city.json').read_text(encoding='utf-8'))
        validate(c)
        c['scenes'][0]['camera']['from']=[0,1]
        with self.assertRaises(ValueError): validate(c)
        c['scenes'][0]['camera']['from']=[0,1,20]
        c['renderer']['backend']='pillow'
        with self.assertRaises(ValueError): validate(c)

    def test_server_asset_paths_cannot_escape_root(self):
        root=Path(__file__).resolve().parent
        self.assertIsNone(safe_asset(root,'../pyproject.toml'))
        self.assertEqual(safe_asset(root,'test_webgl.py'),root/'test_webgl.py')


@unittest.skipUnless(os.environ.get('HVIDEO_TEST_WEBGL')=='1','Set HVIDEO_TEST_WEBGL=1 for real-browser tests')
class WebGLIntegrationTests(unittest.TestCase):
    def test_seek_order_motion_and_resource_cleanup(self):
        from hvideo.webgl import WebGLRenderer
        c=json.loads(files('hvideo').joinpath('templates/cosmic-city.json').read_text(encoding='utf-8'))
        c['video'].update(width=320,height=180)
        with WebGLRenderer(validate(c)) as renderer:
            for a,b in ((1.5,3.8),(7.5,9.5),(12.5,15.5)):
                first=np.asarray(renderer.frame(a))
                moved=np.asarray(renderer.frame(b))
                again=np.asarray(renderer.frame(a))
                np.testing.assert_array_equal(first,again)
                self.assertGreater(np.mean(np.abs(first.astype(float)-moved)),1)
                self.assertGreater(first.std(),5)
            self.assertIn('WebGL 2',renderer.info['webgl'])
            thread=renderer.thread
        self.assertFalse(thread.is_alive())
