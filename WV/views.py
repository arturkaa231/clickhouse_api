from django.shortcuts import render
from wsgiref.util import FileWrapper
from django.http.response import HttpResponse, Http404
from django.template.loader import get_template
from django.template import Context
from django.shortcuts import render_to_response, redirect
from django.template.context_processors import csrf
from django.core.urlresolvers import reverse
from django.contrib import auth
from django.core.paginator import Paginator
from datetime import datetime,date
from gensim.models import Word2Vec
import xlrd
from django.views.decorators.csrf import csrf_exempt
import xlwt
import os.path
import numpy as np
import matplotlib.pyplot as plt
from bokeh.plotting import figure, show, output_file
from bokeh.models import ColumnDataSource, Range1d, LabelSet, Label,Tool
from bokeh.models import CustomJS,TapTool,LassoSelectTool
from bokeh.models.widgets import TextInput
import random
from WV.models import Data,Templates,Options,Tags,ImageOptions
from WV.forms import EnterData,EnterOptions,TagsForm,EnterImageOptionsForm,CentroidForm,SimilarWordForm,MinFrequencyWordForm
from bokeh.plotting import figure, output_file, show
from bokeh.embed import components
import re
from sklearn.datasets import fetch_20newsgroups
from sklearn.manifold import TSNE
from Word2Vec.settings import BASE_DIR,MEDIA_ROOT,STATICFILES_DIRS,STATIC_ROOT
from uuid import uuid4
from sklearn import decomposition
from bokeh.io import export_png,export_svgs
from bokeh.models.sources import AjaxDataSource
from django.http import JsonResponse
import json
from sklearn.cluster import KMeans
from django.core.cache import cache
def Split(tags):
    return tags.split(',')
def MainPage(request):
    args = {}
    args.update(csrf(request))
    args['username'] = auth.get_user(request).username

    if request.method=="POST":
        form_text=EnterData(request.POST, request.FILES)
        form_tg=TagsForm(request.POST)
        if not request.FILES:
            args['form_text'] = EnterData
            args['form'] = TagsForm
            args['error'] = 'Please, add a file'
            return render_to_response('EnterData.html', args)
        #form.article_auth=auth.get_user(request).username

        if  form_text.is_valid() and form_tg.is_valid() :
            form_text.save()
            #разделяем строку с тегами на отдельные теги
            cleaned_tags=Split(request.POST['tg'])

            for i in cleaned_tags:
                tg=Tags(text_id=Data.objects.get(Data_xls=('./'+str(request.FILES['Data_xls']))).id,tg=i)
                tg.save()
            return redirect(reverse('options',args=[Data.objects.get(Data_xls=('./'+str(request.FILES['Data_xls']))).id]))

        else:
            args['form_text'] = EnterData
            args['form'] = TagsForm
            args['error'] = 'The file is not supported. Or bad tags'
            return render_to_response('EnterData.html', args)
    else:
        args['form_text'] = EnterData
        args['form'] = TagsForm
        return render_to_response('EnterData.html', args)

def Enteroptions(request,Data_id):
    args = {}
    args.update(csrf(request))
    args['username'] = auth.get_user(request).username
    if request.method == "POST":
        form = EnterOptions(request.POST)

        #data=Data.objects.get(id=Data_id)
        #xls=data.Data_xls
        if form.is_valid():

            options=form.save(commit=False)
            options.text=Data.objects.get(id=Data_id)
            if 'cbow' in request.POST:
               options.alg=0
            else:
               options.alg=1

            #проверка на повторяющиеся сеты параметров
            if 'cbow' in request.POST:
                for i in Options.objects.filter(text_id=Data_id)[:]:
                    if int(request.POST['size'])==i.size and int(request.POST['win'])== i.win and int(request.POST['minc'])== i.minc   and bool(request.POST['cbow'])==i.cbow:
                        args = {}
                        args.update(csrf(request))
                        args['username'] = auth.get_user(request).username
                        args['form'] = EnterOptions
                        args['templates'] = Templates.objects.all()
                        args['Data_id'] = Data_id
                        args['error'] = 'these parameters already exist'
                        return render_to_response('EnterOptions.html', args)
            else:
                for i in Options.objects.filter(text_id=Data_id)[:]:
                    if int(request.POST['size'])==i.size and int(request.POST['win'])== i.win and int(request.POST['minc'])== i.minc   and bool(request.POST['skipgr'])==i.skipgr:
                        args = {}
                        args.update(csrf(request))
                        args['username'] = auth.get_user(request).username
                        args['form'] = EnterOptions
                        args['templates'] = Templates.objects.all()
                        args['Data_id'] = Data_id
                        args['error'] = 'these parameters already exist'
                        return render_to_response('EnterOptions.html', args)

            form.save()
            Opt_id=options.id
            return redirect(reverse('imageoptions', args=[Data_id,Opt_id]))

    else:
        args['form'] = EnterOptions
        args['templates']=Templates.objects.all()
        args['Data_id']=Data_id
        return render_to_response('EnterOptions.html',args)
def EnterImageOptions(request,Data_id,Opt_id):
    args = {}
    args.update(csrf(request))
    args['username'] = auth.get_user(request).username
    if request.method=='POST':
        form=EnterImageOptionsForm(request.POST)
        data = Data.objects.get(id=Data_id)
        opt=Options.objects.get(id=Opt_id)
        alg=opt.alg

        if form.is_valid():
            imgopt=form.save(commit=False)
            imgopt.opt=Options.objects.get(id=Opt_id)
            data=Data.objects.get(id=Data_id)
            for i in ImageOptions.objects.filter(opt_id=Data_id)[:]:
                if int(request.POST['num_clusters']) == i.num_clusters and int(request.POST['num_neighbors']) == i.num_neighbors:
                    args = {}
                    args.update(csrf(request))
                    args['username'] = auth.get_user(request).username
                    args['form'] = EnterImageOptionsForm

                    args['Data_id'] = Data_id
                    args['Opt_id'] = Opt_id

                    args['error'] = 'these image parameters already exist'
                    return render_to_response('EnterImageOptions.html', args)
            def Map(xls, size, win, minc,alg,num_cl,num_neigh):
                def ChangeName(filename):
                    ext = filename.split('.')[-1]
                    # get filename
                    filename = '{}.{}'.format(uuid4().hex, ext)
                    # return the whole path to the file
                    return filename
                def clean(text):
                    for i in ['/',";","'",'.',',','#', ':', '!', '?','%','^','<','>','&',')','(','{','}',']','[','$','@']:
                        text = text.replace(i, '')
                    text = text.lower()
                    return text

                # Read words from  xls
                def ReadXls(xls):
                    wb = xlrd.open_workbook(os.path.join(xls))
                    wb.sheet_names()
                    sh = wb.sheet_by_index(0)
                    WL = []
                    i = 0
                    while i < sh.nrows:
                        Load = sh.cell(i, 0).value
                        WL.append(Load)
                        i += 1
                    return WL

                # Write to xls
                def WriteXls(xls):
                    # rb=xlrd.open_workbook(a)
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('result')
                    # sheet=book.sheet_by_index(0)
                    # wb=xlcopy(rb)

                    ws = wb.get_sheet(0)
                    k = 0

                    for i in model.wv.vocab.keys():
                        ws.write(k, 0, i)

                        k += 1
                    k = 0

                    for i in model.wv.vocab.keys():
                        ws.write(k, 1, str(model.wv[i]))

                        k += 1
                    wb.save(xls)

                def BuildWordMap():
                    h = .02  # step size in the mesh
                    for weights in ['uniform', 'distance']:
                        # we create an instance of Neighbours Classifier and fit the data.

                        x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
                        y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
                        xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                                             np.arange(y_min, y_max, h))

                        plt.xlim(-1, 1)
                        plt.ylim(-1, 1)
                        plt.title('words map')

                    for i, text in enumerate(model.wv.vocab.keys()):
                        plt.annotate(text, (X[:, 0][i], X[:, 1][i]))
                    plt.show()

                def BuildHtmlMap():
                    freq = []
                    for i in model.wv.vocab:
                        freq.append(model.wv.vocab[i].count)
                    scale = max(freq) /50

                    s1 = ColumnDataSource(data=dict(x=X[:, 0], y=X[:, 1], words=list(model.wv.vocab)))
                    # s1 = ColumnDataSource(data=dict(x=list(X_tsne[:, 0]), y=list(X_tsne[:, 1]), words=sentence,color=['#000000' for i in range(len(sentence))]))
                    p1 = figure(tools="pan,lasso_select,wheel_zoom,undo,reset,save,tap", title="Select Here",
                                plot_width=1000, plot_height=600)
                    p1.scatter(x='x', y='y', size=10, source=s1, alpha=0)

                    def lbset(i, j, size, tcol):
                        x = []
                        x.append(j[0])
                        y = []
                        y.append(j[1])
                        z = []
                        z.append(i)
                        col = []
                        col.append(tcol)
                        s = ColumnDataSource(data=dict(x=x, y=y, words=z, color=col))
                        return LabelSet(x=j[0], y=j[1], text='words', source=s, text_font_size=size,
                                        render_mode='canvas', text_color='color')

                    lbsets = []
                    for i, j in zip(model.wv.vocab, X):
                        lbsets.append(
                            lbset(i, j, str(12 + model.wv.vocab[i].count / scale) + 'pt', word_centroid_map[i]))
                    s1.callback = CustomJS(args=dict(s1=s1), code="""
                                                                         var inds = cb_obj.selected['1d'].indices;
                                                                         var d1 = cb_obj.data;
                                                                         for (i = 0; i < inds.length; i++) {
                                                                            d1['color'][inds[i]]='#DC143C'

                                                                         }
                                                                         s1.change.emit();
                                                                     """)

                    tap = p1.select(type=TapTool)
                    tap.callback = CustomJS(args=dict(s1=s1), code="""
                                                          var inds = cb_obj.selected['1d'].indices;
                                                          var d1 = cb_obj.data;
                                                          for (i = 0; i < inds.length; i++) {
                                                              d1['words'][inds[i]]=''
                                                              d1['x'][inds[i]]=100
                                                          }
                                                          s1.change.emit();
                                                      """)

                    for i in lbsets:
                        p1.add_layout(i)
                    script, div = components(p1)

                    picture_name=ChangeName('.png')

                    export_png(p1,os.path.join(STATIC_ROOT,picture_name))#продакшн STATIC_ROOT
                    imgopt.img = picture_name
                    imgopt.script = script
                    imgopt.div = div

                    form.save()
                    img_id=imgopt.id
                    args['username'] = auth.get_user(request).username
                    args['script'] = script
                    args['div'] = div
                    args['num_clusters']=int(request.POST['num_clusters'])
                    args['num_neighbors'] = int(request.POST['num_neighbors'])
                    args['form']=CentroidForm()
                    args['form2'] = SimilarWordForm()
                    args['form3'] = MinFrequencyWordForm()
                    args['Data_id'] = Data_id
                    args['Img_id'] = img_id
                    args['Opt_id'] = Opt_id
                WL = ReadXls(xls)
                W = []
                # clean from punctuations
                for i in WL:
                    i = clean(i)
                    W.append(i)
                Words = []
                for i in W:
                    i = i.split(' ')
                    Words.append(i)

                # Create the model
                model = Word2Vec(Words, size=size, window=win, min_count=minc,sg=alg)
                modelname=os.path.join(MEDIA_ROOT,ChangeName('.bin'))
                model.save(modelname)
                data.Data_model=modelname
                data.save()

                X = []
                for i in model.wv.vocab.keys():
                    X.append(model.wv[i])
                X = np.array(X)
                tsne = TSNE(n_components=2, perplexity=num_neigh)
                np.set_printoptions(suppress=True)
                X = tsne.fit_transform(X)

                #num_clusters = int(model.wv.syn0.shape[0] / 20)
                num_clusters=num_cl
                kmeans = KMeans(n_clusters=num_clusters)
                idx = kmeans.fit_predict(model.wv.syn0)
                color = []
                for i in range(num_clusters):
                    color.append("#%02X%02X%02X" % (random.randint(0, 255),
                                                    random.randint(0, 255),
                                                    random.randint(0, 255)))
                new_color = []
                for i in idx:
                    new_color.append(color[i])
                # словарь слово:цвет
                word_centroid_map = dict(zip(model.wv.index2word, new_color))
                WriteXls(xls)
                # BuildWordMap()
                BuildHtmlMap()
                return args

            return render_to_response('WordMap.html',Map(os.path.join(MEDIA_ROOT,data.Data_xls.name),opt.size,opt.win,opt.minc,alg,int(request.POST['num_clusters']),int(request.POST['num_neighbors'])))
    else:
        args = {}
        args.update(csrf(request))
        args['username'] = auth.get_user(request).username
        args['form'] = EnterImageOptionsForm

        args['Data_id'] = Data_id
        args['Opt_id'] = Opt_id

        return render_to_response('EnterImageOptions.html', args)

def Template(request,size,win,minc,Data_id):
    args={}
    args.update(csrf(request))
    args['username'] = auth.get_user(request).username
    args['form'] = EnterOptions
    args['templates'] = Templates.objects.all()
    args['size']=size
    args['win'] = win
    args['minc'] = minc
    args['Data_id']=Data_id
    return render_to_response('EnterOptions.html', args)

def DownloadedTexts(request,page_number=1):
    args={}
    args.update(csrf(request))
    args['username'] = auth.get_user(request).username
    if request.method=="POST" :
        form=TagsForm(request.POST)
        if form.is_valid():
            return redirect(reverse('FilteredTexts',args=[1,request.POST['tg']]))
        else:
            all_texts = Data.objects.all().order_by('-id')
            args['texts'] = Paginator(all_texts, 10).page(page_number)
            args['form'] = TagsForm

            return render_to_response('DownloadedTexts.html', args)
    else:
        all_texts = Data.objects.all().order_by('-id')
        args['texts'] = Paginator(all_texts, 10).page(page_number)
        args['form']=TagsForm

        return render_to_response('DownloadedTexts.html',args)

def FilteredTexts(request, page_number=1,tags=''):
    args = {}
    args.update(csrf(request))
    args['username'] = auth.get_user(request).username

    if request.method == "POST":
        form = TagsForm(request.POST)
        if form.is_valid():
            return redirect(reverse('FilteredTexts',args=[1,request.POST['tg']]))
        else:
            args['tags'] = tags
            args['texts'] =None
            args['form'] = TagsForm

            return render_to_response('FilteredTexts.html', args)
    else:
        cleaned_tags = Split(tags)
        data=Data.objects
        for i in cleaned_tags:
            data=data.filter(TAGS__tg=i)
        args['tags'] = tags
        args['texts'] = Paginator(data.all(),10).page(page_number)
        args['form'] = TagsForm

        return render_to_response('FilteredTexts.html', args)

def Maps(request,Data_id,page_number=1):
    args={}
    args.update(csrf(request))
    args['username'] = auth.get_user(request).username
    # Добавление пагинации
    all_options = Options.objects.filter(text_id=Data_id)
    args['options'] = Paginator(all_options,2).page(page_number)
    args['Data_id']=Data_id

    args['text']=Data.objects.get(id=Data_id)
    return render_to_response('maps.html',args)

def Images(request,Data_id,Opt_id,page_number=1):

    args={}
    args.update(csrf(request))
    args['username'] = auth.get_user(request).username
    # Добавление пагинации
    all_images = ImageOptions.objects.filter(opt_id=Opt_id)
    args['images'] = Paginator(all_images,1).page(page_number)
    args['Data_id']=Data_id

    args['opt']=Options.objects.get(id=Opt_id)

    return render_to_response('images.html',args)

def Showmap(request,Data_id,Opt_id,Img_id):
    args = {}
    args.update(csrf(request))
    args['username'] = auth.get_user(request).username
    #html=Options.objects.get(id=Opt_id).html
    script=ImageOptions.objects.get(id=Img_id).script
    div = ImageOptions.objects.get(id=Img_id).div
    args['script'] = script
    args['div'] = div
    args['Opt_id'] = Opt_id
    args['Data_id'] = Data_id

    args['Img_id'] = Img_id
    args['num_clusters']=ImageOptions.objects.get(id=Img_id).num_clusters
    args['num_neighbors'] = ImageOptions.objects.get(id=Img_id).num_neighbors
    args['form']=CentroidForm()
    args['form2'] = SimilarWordForm()
    args['form3'] = MinFrequencyWordForm()
    return render_to_response("WordMap.html",args)

def DeleteOpt(request,Opt_id, Data_id):
    options=Options.objects.get(id=Opt_id)
    options.delete()
    return redirect(reverse('maps',args=[Data_id,1]))

def DeleteImageOpt(request,Data_id,Opt_id, Img_id):
    images=ImageOptions.objects.get(id=Img_id)
    images.delete()
    return redirect(reverse('images',args=[Data_id,Opt_id,1]))

def SetPreview(request,Data_id, Opt_id,img):
    option=Options.objects.get(id=Opt_id)
    option.preview=img
    option.save()
    return redirect(reverse('images', args=[Data_id, Opt_id, 1]))
#Задание центроид руками
def Centroids(request,Data_id,Opt_id,Img_id):
    args = {}
    args.update(csrf(request))
    args['username'] = auth.get_user(request).username
    if request.method == 'POST':
        form = CentroidForm(request.POST)
        data = Data.objects.get(id=Data_id)
        opt = Options.objects.get(id=Opt_id)

        if form.is_valid():
            imgopt =ImageOptions.objects.get(id=Img_id)
            imgopt.opt = Options.objects.get(id=Opt_id)
            num_clusters = ImageOptions.objects.get(id=Img_id).num_clusters
            num_neighbors = ImageOptions.objects.get(id=Img_id).num_neighbors
            model = Word2Vec.load(data.Data_model.name)
            centroids = Split(request.POST['centroids'])
            for i in centroids:
                if i not in model.wv.vocab:
                    args['username'] = auth.get_user(request).username
                    args['script'] = imgopt.script
                    args['div'] = imgopt.div
                    args['Img_id'] = Img_id
                    args['error'] = "Bad centroids(Must be in vocabulary and separated by commas)"
                    args['form'] = CentroidForm()
                    args['form2'] = SimilarWordForm()
                    args['form3'] = MinFrequencyWordForm()
                    args['Data_id'] = Data_id
                    args['Opt_id'] = Opt_id
                    args['num_clusters'] = imgopt.num_clusters
                    args['num_neighbors'] = imgopt.num_neighbors
                return render_to_response('WordMap.html',
                                          args)

            # Удаляем старое изображение
            imgopt.delete()
            def Map(num_cl,num_neigh,centerwords):
                # Write to xls
                def WriteXls(xls):
                    # rb=xlrd.open_workbook(a)
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('result')
                    # sheet=book.sheet_by_index(0)
                    # wb=xlcopy(rb)

                    ws = wb.get_sheet(0)
                    k = 0

                    for i in model.wv.vocab.keys():
                        ws.write(k, 0, i)

                        k += 1
                    k = 0

                    for i in model.wv.vocab.keys():
                        ws.write(k, 1, str(model.wv[i]))

                        k += 1
                    wb.save(xls)

                def BuildHtmlMap():
                    freq = []
                    for i in model.wv.vocab:
                        freq.append(model.wv.vocab[i].count)
                    scale = max(freq) / 50

                    s1 = ColumnDataSource(data=dict(x=X[:, 0], y=X[:, 1], words=list(model.wv.vocab)))
                    # s1 = ColumnDataSource(data=dict(x=list(X_tsne[:, 0]), y=list(X_tsne[:, 1]), words=sentence,color=['#000000' for i in range(len(sentence))]))
                    p1 = figure(tools="pan,lasso_select,wheel_zoom,undo,reset,save,tap", title="Select Here",
                                plot_width=1000, plot_height=600)
                    p1.scatter(x='x', y='y', size=10, source=s1, alpha=0)

                    def lbset(i, j, size, tcol):
                        x = []
                        x.append(j[0])
                        y = []
                        y.append(j[1])
                        z = []
                        z.append(i)
                        col = []
                        col.append(tcol)
                        s = ColumnDataSource(data=dict(x=x, y=y, words=z, color=col))
                        return LabelSet(x=j[0], y=j[1], text='words', source=s, text_font_size=size,
                                        render_mode='canvas', text_color='color')

                    lbsets = []
                    for i, j in zip(model.wv.vocab, X):
                        if i in centerwords:
                            a='#000000'
                        else:
                            a = word_centroid_map[i]

                        lbsets.append(

                            lbset(i, j, str(12 + model.wv.vocab[i].count / scale) + 'pt', a))
                    s1.callback = CustomJS(args=dict(s1=s1), code="""
                                                                             var inds = cb_obj.selected['1d'].indices;
                                                                             var d1 = cb_obj.data;
                                                                             for (i = 0; i < inds.length; i++) {
                                                                                d1['color'][inds[i]]='#DC143C'

                                                                             }
                                                                             s1.change.emit();
                                                                         """)

                    tap = p1.select(type=TapTool)
                    tap.callback = CustomJS(args=dict(s1=s1), code="""
                                                              var inds = cb_obj.selected['1d'].indices;
                                                              var d1 = cb_obj.data;
                                                              for (i = 0; i < inds.length; i++) {
                                                                  d1['words'][inds[i]]=''
                                                                  d1['x'][inds[i]]=100
                                                              }
                                                              s1.change.emit();
                                                          """)

                    for i in lbsets:
                        p1.add_layout(i)
                    script, div = components(p1)

                    def ChangeName(filename):
                        ext = filename.split('.')[-1]
                        # get filename
                        filename = '{}.{}'.format(uuid4().hex, ext)
                        # return the whole path to the file
                        return filename

                    picture_name = ChangeName('.png')

                    export_png(p1, os.path.join(STATIC_ROOT, picture_name))  # продакшн STATIC_ROOT
                    imgopt = ImageOptions.objects.create(id=Img_id)
                    imgopt.img = picture_name

                    imgopt.num_clusters = num_cl
                    imgopt.num_neighbors = num_neigh
                    imgopt.opt = Options.objects.get(id=Opt_id)
                    imgopt.script = script
                    imgopt.div = div
                    imgopt.save()

                    args['username'] = auth.get_user(request).username
                    args['script'] = script
                    args['div'] = div
                    args['Img_id'] = Img_id
                    args['form'] = CentroidForm()
                    args['form2'] = SimilarWordForm()
                    args['form3'] = MinFrequencyWordForm()
                    args['Data_id'] = Data_id
                    args['Opt_id'] = Opt_id
                    args['num_clusters'] = num_cl
                    args['num_neighbors'] = num_neigh


                X = []
                for i in model.wv.vocab.keys():
                    X.append(model.wv[i])
                X = np.array(X)

                tsne = TSNE(n_components=2, perplexity=num_neigh)
                np.set_printoptions(suppress=True)
                X = tsne.fit_transform(X)

                centers=[]
                for i in centerwords:
                    centers.append(model.wv[i])

                centers=np.array(centers)

                # centers =np.array((model.wv.syn0[1],model.wv.syn0[15],model.wv.syn0[0]), np.float64)
                # num_clusters = int(model.wv.syn0.shape[0] / 20)
                num_clusters = num_cl
                kmeans = KMeans(n_clusters=num_clusters,n_init=1,init=centers)
                #kmeans = KMeans(n_clusters=num_clusters)
                idx = kmeans.fit_predict(model.wv.syn0)

                color = []
                for i in range(num_clusters):
                    color.append("#%02X%02X%02X" % (random.randint(0, 255),
                                                    random.randint(0, 255),
                                                    random.randint(0, 255)))
                new_color = []
                for i in idx:
                    new_color.append(color[i])
                # словарь слово:цвет
                word_centroid_map = dict(zip(model.wv.index2word, new_color))
                # WriteXls(xls)
                # BuildWordMap()
                BuildHtmlMap()
                return args
            return render_to_response('WordMap.html',
                                      Map(int(num_clusters),int(num_neighbors),centroids))
@csrf_exempt
def SimilarWords(request):
    if request.method=='POST':
        word=request.POST.get('word')
        Data_id=request.POST.get('Data_id')

        model=Word2Vec.load(Data.objects.get(id=int(Data_id)).Data_model.name)

        response_data = {}
        response_data['word1']=model.wv.most_similar(word)[0]
        response_data['word2'] = model.wv.most_similar(word)[1]
        response_data['word3'] = model.wv.most_similar(word)[2]
        response_data['word4'] = model.wv.most_similar(word)[3]
        response_data['word5'] = model.wv.most_similar(word)[4]
        response_data['word6'] = model.wv.most_similar(word)[5]
        response_data['word7'] = model.wv.most_similar(word)[6]

        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json"
        )
def MinFrequencyWord(request,Data_id,Opt_id,Img_id):
    args = {}
    args.update(csrf(request))
    args['username'] = auth.get_user(request).username
    if request.method == 'POST':
        form = MinFrequencyWordForm(request.POST)
        data = Data.objects.get(id=Data_id)



        if form.is_valid():
            imgopt = ImageOptions.objects.get(id=Img_id)

            num_clusters= ImageOptions.objects.get(id=Img_id).num_clusters
            num_neighbors = ImageOptions.objects.get(id=Img_id).num_neighbors
            #Удаляем старое изображение
            imgopt.delete()
            def Map(num_cl,num_neigh,minfreq):
                # Write to xls

                def BuildHtmlMap():
                    freq = []
                    for i in model.wv.vocab:
                        freq.append(model.wv.vocab[i].count)
                    scale = max(freq) / 50

                    s1 = ColumnDataSource(data=dict(x=X[:, 0], y=X[:, 1], words=words))
                    # s1 = ColumnDataSource(data=dict(x=list(X_tsne[:, 0]), y=list(X_tsne[:, 1]), words=sentence,color=['#000000' for i in range(len(sentence))]))
                    p1 = figure(tools="pan,lasso_select,wheel_zoom,undo,reset,save,tap", title="Select Here",
                                plot_width=1000, plot_height=600)
                    p1.scatter(x='x', y='y', size=10, source=s1, alpha=0)

                    def lbset(i, j, size, tcol):
                        x = []
                        x.append(j[0])
                        y = []
                        y.append(j[1])
                        z = []
                        z.append(i)
                        col = []
                        col.append(tcol)
                        s = ColumnDataSource(data=dict(x=x, y=y, words=z, color=col))
                        return LabelSet(x=j[0], y=j[1], text='words', source=s, text_font_size=size,
                                        render_mode='canvas', text_color='color')

                    lbsets = []
                    for i, j in zip(words, X):
                        lbsets.append(

                            lbset(i, j, str(12 + model.wv.vocab[i].count / scale) + 'pt', word_centroid_map[i]))
                    s1.callback = CustomJS(args=dict(s1=s1), code="""
                                                                                 var inds = cb_obj.selected['1d'].indices;
                                                                                 var d1 = cb_obj.data;
                                                                                 for (i = 0; i < inds.length; i++) {
                                                                                    d1['color'][inds[i]]='#DC143C'

                                                                                 }
                                                                                 s1.change.emit();
                                                                             """)

                    tap = p1.select(type=TapTool)
                    tap.callback = CustomJS(args=dict(s1=s1), code="""
                                                                  var inds = cb_obj.selected['1d'].indices;
                                                                  var d1 = cb_obj.data;
                                                                  for (i = 0; i < inds.length; i++) {
                                                                      d1['words'][inds[i]]=''
                                                                      d1['x'][inds[i]]=100
                                                                  }
                                                                  s1.change.emit();
                                                              """)

                    for i in lbsets:
                        p1.add_layout(i)
                    script, div = components(p1)

                    def ChangeName(filename):
                        ext = filename.split('.')[-1]
                        # get filename
                        filename = '{}.{}'.format(uuid4().hex, ext)
                        # return the whole path to the file
                        return filename

                    picture_name = ChangeName('.png')
                    export_png(p1, os.path.join(STATIC_ROOT, picture_name))  # продакшн STATIC_ROOT
                    #Создаем новое изображение
                    imgopt=ImageOptions.objects.create(id=Img_id)
                    imgopt.img = picture_name

                    imgopt.num_clusters=num_cl
                    imgopt.num_neighbors = num_neigh
                    imgopt.opt=Options.objects.get(id=Opt_id)
                    imgopt.script = script
                    imgopt.div = div
                    imgopt.save()

                    args['username'] = auth.get_user(request).username
                    args['script'] = script
                    args['div'] = div
                    args['Img_id'] = imgopt.id
                    args['form'] = CentroidForm()
                    args['form2'] = SimilarWordForm()
                    args['form3'] = MinFrequencyWordForm()
                    args['Data_id'] = Data_id
                    args['Opt_id'] = Opt_id
                    args['num_clusters'] =num_cl
                    args['num_neighbors'] = num_neigh

                # Create the model
                model = Word2Vec.load(data.Data_model.name)
                words = []

                for i in model.wv.vocab:
                    if model.wv.vocab[i].count > minfreq:
                        words.append(i)
                vectors = [model[w] for w in words]



                tsne = TSNE(n_components=2, perplexity=num_neigh)
                np.set_printoptions(suppress=True)
                X = tsne.fit_transform(vectors)

                # centers =np.array((model.wv.syn0[1],model.wv.syn0[15],model.wv.syn0[0]), np.float64)
                # num_clusters = int(model.wv.syn0.shape[0] / 20)
                num_clusters = num_cl
                kmeans = KMeans(n_clusters=num_clusters)
                # kmeans = KMeans(n_clusters=num_clusters)
                idx = kmeans.fit_predict(vectors)
                color = []
                for i in range(num_clusters):
                    color.append("#%02X%02X%02X" % (random.randint(0, 255),
                                                    random.randint(0, 255),
                                                    random.randint(0, 255)))
                new_color = []
                for i in idx:
                    new_color.append(color[i])
                # словарь слово:цвет
                word_centroid_map = dict(zip(model.wv.index2word, new_color))
                # WriteXls(xls)
                # BuildWordMap()
                BuildHtmlMap()
                return args


            return render_to_response('WordMap.html',
                                      Map(int(num_clusters),int(num_neighbors),int(request.POST['freq'])))
def DownloadText(request,Data_id):

    filename =Data.objects.get(id=Data_id).Data_xls.name
    content_type = 'application/vnd.ms-excel'
    file_path = os.path.join(MEDIA_ROOT, filename)
    response = HttpResponse(FileWrapper(open(file_path,'rb')), content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename=%s' % ( filename)
    response['Content-Length'] = os.path.getsize(file_path)
    return response
