import errno
import asyncio
import json
import logging
import os
import sys
import time
from subprocess import call

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

if sys.platform.startswith('linux'):
    logging.info("Linux OS Detected, running test will be disabled.")
    SAVE_FOLDER = os.path.normpath(os.getcwd() + '/TingusData' + '/save_files')
else:
    import pyautogui
    from lackey import click as _click
    from lackey import doubleClick as _doubleClick
    from lackey import rightClick as _rightClick
    from lackey import wait as _wait
    from lackey import Pattern
    SAVE_FOLDER = os.path.normpath(os.getenv("PROGRAMDATA") + '/TingusData' + '/save_files/')

try:
    with open("settings.json") as settings_file:
        SETTINGS_FILE = json.load(settings_file)
except:
    raise Exception("NO SETTINGS JSON FILE FOUND")

class Main_Routes:
    def __init__(self, web, server_state):
        self.web = web
        self.server_state = server_state
        self.FileHandling = FileHandling()

    def formatResponse(self, data):
        ret = {
            "result": 'HARDCODED VALUES RESULT',
            "msg": 'HARDCODED VALUES MSG',
            "data": data
        }

        return ret

    async def screenshotTool(self, request):
        payload = await request.json()
        delay = payload['delay']

        if delay >= 1:
            await asyncio.sleep(delay)

        if self.server_state['mode'] == 'development':
            if sys.platform == 'win32':
                call(['py', '-3', '../apps/Screenshot_Tool/main.py', '--save', os.path.normpath(SAVE_FOLDER + '/images/')])
        else:
            call(['./Screenshot_Tool/Screenshot_Tool.exe', '--save', os.path.normpath(SAVE_FOLDER + '/images/')])

        return self.web.json_response("Done")

    async def getTestsCount(self, request):
        return self.web.json_response(self.formatResponse(len(os.listdir(os.path.normpath(SAVE_FOLDER + '/tests/')))))

    async def getSuitesCount(self, request):
        return self.web.json_response(self.formatResponse(len(os.listdir(os.path.normpath(SAVE_FOLDER + '/suites/')))))

    async def getTests(self, request):
        return self.web.json_response(self.formatResponse(self._getTests()))
    
    def _getTests(self):
        tests = []
        for file in os.listdir(os.path.normpath(SAVE_FOLDER + '/tests/')):
            description = json.load(open(os.path.normpath(SAVE_FOLDER + '/tests/' + file)))['description']
            tests.append({ 'name' : file[:-5], 'description': description, 'type': 'test'})
        return tests

    async def getSuites(self, request):
        return self.web.json_response(self.formatResponse(self._getSuites()))

    def _getSuites(self):
        tests = []
        for file in os.listdir(os.path.normpath(SAVE_FOLDER + '/suites/')):
            description = json.load(open(os.path.normpath(SAVE_FOLDER + '/suites/' + file)))['description']
            tests.append({ 'name': file[:-5], 'description': description, 'type': 'suite'})
        return tests

    async def getImages(self, request):
        images = []
        for file in os.listdir(os.path.normpath(SAVE_FOLDER + '/images/')):
            if not file.endswith('.json'):
                images.append({"name": file[:-4]})
        return self.web.json_response(self.formatResponse(images))

    async def saveTest(self, model):
        payload = await model.json()
        payload = payload['model']
        with self.FileHandling.safe_open_w(os.path.normpath(SAVE_FOLDER + '/tests/' + payload['name'] + '.json')) as fp:
            json.dump(payload, fp, indent=4)

        return self.web.json_response({'Status': 'Saved'})

    async def saveTestSuite(self, model):
        payload = await model.json()
        payload = payload['model']
        with self.FileHandling.safe_open_w(os.path.normpath(SAVE_FOLDER + '/suites/' + payload['name'] + '.json')) as fp:
            json.dump(payload, fp, indent=4)

        return self.web.json_response({'Status': 'Saved'})

    async def loadTestSuite(self, test_name):
        payload = await test_name.json()
        payload = payload['test_name']
        return self.web.json_response(self.formatResponse(self._load_test_suite(payload)))

    def _load_test_suite(self, test_name):
        json_data = open(os.path.normpath(SAVE_FOLDER + '/suites/' + test_name + '.json'))
        return json.load(json_data)

    async def loadTest(self, test_name):
        payload = await test_name.json()
        payload = payload['test_name']
        return self.web.json_response(self.formatResponse(self._load_test(payload)))

    def _load_test(self, test_name):
        json_data = open(os.path.normpath(SAVE_FOLDER + '/tests/' + test_name + '.json'))
        return json.load(json_data)

    async def runTestSuite(self, model):
        # sorted(list_to_be_sorted, key=lambda k: k['order'])
        # Load all the test before you begin to execute them. So that the tests are equally as fast.
        payload = await model.json()
        payload = payload['model']

        return self.web.json_response(self.formatResponse(self._runTestSuite(payload)))

    if sys.platform == "linux" or sys.platform == "linux2":
        logging.info("Run Test Suite disabled")
    else:
        def _runTestSuite(self, model):
            suite_results = []
            print('_runTestSuite Model: ', model)
            for index, test in enumerate(model['tests']):
                if test['type'] == 'suite':
                    test_suite = self._load_test_suite(test['name'])
                    suite_results.append({
                        "name": test_suite["name"],
                        "index": index,
                        "type": "suite",
                        "results": self._runTestSuite(test_suite)
                    })
                elif test['type'] == 'test':
                    test_ = self._load_test(test['name'])
                    suite_results.append({
                        "name": test_["name"],
                        "index": index,
                        "type": "test",
                        "results": self._run_test(test_)
                    })
            print("Test Results: ", suite_results)

            return suite_results

    async def runTest(self, model):
        payload = await model.json()
        payload = payload['model']

        return self.web.json_response(self.formatResponse(self._run_test(payload)))

    if sys.platform == "linux" or sys.platform == "linux2":
        logging.info("Run Test Suite disabled")
    else:
        def _run_test(self, model):
            test_result =  {
                "failed_actions": [],
                "success_actions": []
            }
            time.sleep(SETTINGS_FILE.get("testSettings", {}).get("runTestDelay", 5))
            for index, action in enumerate(model['actions']):
                if action['action'] in ['click', 'r_click', 'doubleclick', 'wait', 'clickwait']:
                    image_meta = ImageJson(action['data'])
                try:
                    if action['action'] == 'click':
                        for _ in range(int(action.get('repeat', '1') or '1')):
                            _wait(os.path.normpath(SAVE_FOLDER + '/images/' + action['data'] + '.png'), int(action['delay']))
                            _click(Pattern(os.path.normpath(SAVE_FOLDER + '/images/' + action['data'] + '.png')).targetOffset(image_meta.get_click_offset()[0], image_meta.get_click_offset()[1]))
                    if action['action'] == 'r_click':
                        for _ in range(int(action.get('repeat', '1') or '1')):
                            _wait(os.path.normpath(SAVE_FOLDER + '/images/' + action['data'] + '.png'), int(action['delay']))
                            _rightClick(Pattern(os.path.normpath(SAVE_FOLDER + '/images/' + action['data'] + '.png')).targetOffset(image_meta.get_click_offset()[0], image_meta.get_click_offset()[1]))
                    if action['action'] == 'doubleclick':
                        for _ in range(int(action.get('repeat', '1') or '1')):
                            _wait(os.path.normpath(SAVE_FOLDER + '/images/' + action['data'] + '.png'), int(action['delay']))
                            _doubleClick(Pattern(os.path.normpath(SAVE_FOLDER + '/images/' + action['data'] + '.png')).targetOffset(image_meta.get_click_offset()[0], image_meta.get_click_offset()[1]))
                    if action['action'] == 'wait':
                        for _ in range(int(action.get('repeat', '1') or '1')):
                            _wait(os.path.normpath(SAVE_FOLDER + '/images/' + action['data'] + '.png'), int(action['delay']))
                    if action['action'] == 'clickwait':
                        for _ in range(int(action.get('repeat', '1') or '1')):
                            _wait(os.path.normpath(SAVE_FOLDER + '/images/' + action['data'] + '.png'), int(action['delay']))
                            _click(Pattern(os.path.normpath(SAVE_FOLDER + '/images/' + action['data'] + '.png')).targetOffset(image_meta.get_click_offset()[0], image_meta.get_click_offset()[1]))
                    if action['action'] == 'type':
                        for _ in range(int(action.get('repeat', '1') or '1')):
                            pyautogui.typewrite(action['data'])
                    if action['action'] == 'keycombo':
                        keys = action['data'].split('+')
                        for _ in range(int(action.get('repeat', '1') or '1')):
                            pyautogui.hotkey(*keys)
                    if action['action'] == 'keypress':
                        for _ in range(int(action.get('repeat', '1') or '1')):
                            pyautogui.typewrite(action['data'])
                    if action['action'] == 'close':
                        for _ in range(int(action.get('repeat', '1') or '1')):
                            pyautogui.hotkey('alt', 'f4')
                    test_result["success_actions"].append({
                        "index": index,
                        "action": action["action"],
                        "data": action["data"]
                    })
                except Exception as ex:
                    test_result["failed_actions"].append({
                        "index": index,
                        "action": action["action"],
                        "data": action["data"],
                        "error": str(ex.__doc__)
                    })
            return test_result

    async def searchTests(self, search_term):
        payload = await search_term.json()
        payload = payload['search_term']
        tests = self._getTests()
        tests_ = []
        for test in tests:
            if test['name'].lower().find(payload.lower()) > -1:
                tests_.append(test)
        return self.web.json_response(self.formatResponse(tests_))

    async def searchSuites(self, search_term):
        payload = await search_term.json()
        payload = payload['search_term']
        suites = self._getSuites()
        suites_ = []
        for suite in suites:
            if suite['name'].lower().find(payload.lower()) > -1:
                suites_.append(suite)
        return self.web.json_response(self.formatResponse(suites_))


class FileHandling:
    """Better why to handle files that needs to be saved etc.
    The function below safe_open() take a path and will check if path exist.
    If it doesn't, it will attempt to create the folders.
    EXAMPLE USAGE: with safe_open_w('/Users/bill/output/output-text.txt') as f:
                       f.write(stuff_to_file)
    """
    def _mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def safe_open_w(self, path):
        ''' Open "path" for writing, creating any parent directories as needed.
        '''
        self._mkdir_p(os.path.dirname(path))
        return open(path, 'w')

    def safe_create_path(self, path):
        '''Create Path give if doesn't exist
        '''
        self._mkdir_p(os.path.dirname(path))
        return path


class ImageJson:
    def __init__(self, image_name):
        self.image_meta = self._read_json(image_name)

    def _read_json(self, image_name):
        with open(os.path.normpath(SAVE_FOLDER + '/images/' + image_name + '.json')) as f:
            return json.load(f)

    def get_click_offset(self):
        return self.image_meta['clickOffset']
