import aiohttp
import asyncio
import uvicorn
import base64
from fastai import *
from fastai.vision import *
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

#export_file_url = 'https://www.dropbox.com/s/6bgq8t6yextloqp/export.pkl?raw=1'
export_file_url1 = 'https://drive.google.com/uc?export=download&id=14n2pq1gmVmMePtOkiIwdiYMV-UPH77uS'
export_file_name1 = 'resnet34_clscatdog.pkl'
export_file_url2 = 'https://drive.google.com/uc?export=download&id=1A8m2KfyGF5TcX6Ws8eCCvALcl19Z7LCg'
export_file_name2 = 'resnet34_clsimagenet.pkl'

#classes = ['black', 'grizzly', 'teddys']
path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner1():
    await download_file(export_file_url1, path / 'models' / export_file_name1)
    try:
        learn1 = load_learner(path/'models', export_file_name1)
        return learn1
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


async def setup_learner2():
    await download_file(export_file_url2, path / 'models' / export_file_name2)
    try:
        learn2 = load_learner(path/'models', export_file_name2)
        return learn2
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner1()), asyncio.ensure_future(setup_learner2())]
#learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
learn1, learn2 = loop.run_until_complete(asyncio.gather(*tasks))
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    data = await request.form()
    #print(data)

    #if data['file'] is not None:
    if 'file' in data.keys():
      img_bytes = await (data['file'].read())
      img = open_image(BytesIO(img_bytes))
    elif 'image' in data.keys():
      imgdata = re.sub('^data:image/.+;base64,', '', data['image'])
      imgdata = base64.b64decode(imgdata)
      img = open_image(BytesIO(imgdata))
      #img = Image.open(io.BytesIO(imgdata))
    else:
        return JSONResponse({'result': 'NA', 'accuracy': 0.0})
    
    print(img.shape)
    pred_class,pred_idx,preds = learn1.predict(img)
    acc = preds[pred_idx].item()
    if acc < 0.4:#probably not cat or dog
        pred_class,pred_idx,preds = learn2.predict(img)#predict using imagenet classifier on 1000 possible classes
        preds_sorted, idxs = preds.sort(descending=True)[:3]

        pred_2_class = learn2.data.classes[idxs[1]]
        pred_3_class = learn2.data.classes[idxs[2]]

        pred_1_prob = np.round(100*preds_sorted[0].item(),2)
        pred_2_prob = np.round(100*preds_sorted[1].item(),2)
        pred_3_prob = np.round(100*preds_sorted[2].item(),2)
        preds_best3 = [f'{pred_class} ({pred_1_prob}%)', f'{pred_2_class} ({pred_2_prob}%)', f'{pred_3_class} ({pred_3_prob}%)']

        result = f'I think it is not cat nor dog.\n Probably: (1st) {preds_best3[0]}\n(2nd) {preds_best3[1]}\n(3rd) {preds_best3[2]}'

    else:
        acc = np.round(100*acc,2)
        result = f'{str(pred_class)} ({acc}%)'
    return JSONResponse({'result': result, 'accuracy': acc})


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
