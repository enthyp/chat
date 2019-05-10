# Chat
Chat server with online toxic message detection.

## Running.
  * Run ai-service:  
    `twistd --nodaemon --python chat/server/ai_service.py`
    BTW: _nodaemon_ option runs service in the terminal process, you can run in background if you remove that option and add `--pidfile=ai --log=ai`. `ai.pid` then contains PID of the service (kill it when you're done).
  * Run chat-service:  
    `twistd --python chat/server/chat_service.py`
    Same as above applies to running in the background.
  * Run client:
    `python chat/client.py 8080`

## Development.
### Prerequisites.
1. cd to top level project directory.  

2. Create new conda environment from `environment.yml` file:  
	`conda env create -n chat_env -f=environment.yml`

3. Activate new environment:  
   `conda activate chat_env`

4. Install __ai__ and __chat__ packages in editable mode:  
   `pip install -e .`

### Workflow.
__Locally__:  
1. Create new branch from __chat_dev__ branch (naming convention: __feature/feature_name__):  
    `git checkout chat_dev`  
    `git checkout -b feature/feature_name`

2. Make some changes:  
    `git add file1 file2...`  
    `git commit -m "Best commit ever..."`

3. Push to your forked repo (`-u` option to set remote tracking branch):  
    `git push -u origin feature/feature_name`  

__On GitHub__ - once you have the feature ready for merge:  
 
4. Create a PR from __origin:feature/feature_name__ to __upstream:chat_dev__.  

5. Once PR is merged, pull changes to your local git repo and push them onto your fork:  
    `git pull upstream chat_dev`  
    `git push origin chat_dev`  

6. Clean up your working branches (from another branch):  
    `git branch -d feature/feature_name`  
    `git push --delete origin feature/feature_name`  

## Notes:  
* Before you create a new branch from chat_dev - do `git pull upstream chat_dev`.
* If you add new dependency, e.g. `scikit-learn` - add it to `requirements.txt` and `environment.yml` files.
