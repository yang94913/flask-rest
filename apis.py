import uuid

import os
from flask import request, session
from flask_restful import Api, Resource, marshal_with, fields, marshal, reqparse
from sqlalchemy import or_
from werkzeug.datastructures import FileStorage

import settings
from models import User, Image, Music
from dao import query, queryAll, add, queryById, delete, deleteById

api = Api()

def init_api(app):
    api.init_app(app)

class UserApi(Resource):
    def get(self):

        key = request.args.get('key')
        if key:
            result = {'state':'fail',
                    'msg':'查无数据'}

            # 搜索用户信息
            qs = query(User).filter(or_(User.id == key,User.name == key,User.phone == key))
            if qs.count():
                result['state'] = 'ok'
                result['msg'] = '查询成功'
                result['data'] = qs.first().json
            return result
        # 从数据库中查询所有的用户
        users = queryAll(User)
        return {'state':'ok',
                'data':[user.json for user in users]}
    def post(self):
        # 从上传的form对象中取出name和phone
        name = request.form.get('name')
        phone = request.form.get('phone')

        print(name,phone)
        # 数据存入到数据库
        user = User()
        user.name = name
        user.phone = phone

        add(user)

        return {"state":"ok",
                "msg":'添加{}成功'.format(name)}

    def delete(self):
        id = request.args.get('id')
        # user = queryById(User,id) # 是否考虑 id 不存在的情况
        # delete(user)

        flag = deleteById(User,id)

        return {'state':'ok',
                'flag':'flag',
                'msg':'删除{}成功'.format(id)}

    def put(self):
        id = request.form.get('id')
        user = queryById(User,id)
        user.name = request.form.get('name')
        user.phone = request.form.get('phone')

        add(user)

        return {'state':'ok',
                'msg':user.name+'更新成功'}

class ImageApi(Resource):
    img_fields = {"id":fields.Integer,
                  "name":fields.String,
                  "url":fields.String,
                  "size":fields.Integer(default=0)}
    get_out_fields = {
        "state":fields.String(default='ok'),
        "data":fields.Nested(img_fields),
        "size":fields.Integer(default=1)
    }

    # @marshal_with(out_fields)
    def get(self):

        id = request.args.get('id')
        if id:
            img = query(Image).filter(Image.id==id).first()
            return marshal(img,self.img_fields)
        else:
            images = queryAll(Image)

            data={"data":images,
                     "size":len(images) }

            # 向session中存放用户名
            session['login_name'] = 'disen'
        return marshal(data,self.get_out_fields)


    parser = reqparse.RequestParser()
    parser.add_argument('name',required=True,help='必须提供图片名称参数')
    parser.add_argument('url', required=True, help='必须提供已上传图片的路径')
    def post(self):
        args = self.parser.parse_args()

        img = Image()
        img.name = args.get('name')
        img.url = args.get('url')

        add(img)
        return {'msg':'添加图片成功'}

class MusicApi(Resource):
    parser = reqparse.RequestParser()

    # 向参数
    parser.add_argument('name',dest='name',type=str,required=True,help='必须提供name关键字')
    parser.add_argument('id',type=int,help='请确定id为数值型')
    parser.add_argument('tag',action='append',required=True,help='至少提供一个tag标签')
    parser.add_argument('session',location='cookies',help='cookie中不存在session')

    # 定制输出
    music_fields = {
        'id':fields.Integer,
        'name':fields.String,
        'singer':fields.String,
        'url': fields.String(attribute='mp3_url')
    }
    out_fields = {
        'state':fields.String(default='ok'),
        'msg':fields.String(default='查询成功'),
        'data':fields.Nested(music_fields)
  }
    @marshal_with(out_fields)
    def get(self):
        # 按name搜索
        # 通过request参数解析器，开始解析请求参数
        args = self.parser.parse_args()

        name = args.get('name')
        tags = args.get('tag')

        session = args.get('session')
        print('session->', session)

        musics = query(Music).filter(Music.name.like('%{}%'.format(name)))
        if musics.count():
            return {'data':musics.all()}

        return {'msg':'搜索{}音乐不存在,标签'.format(name,tags)}

class UploadApi(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument("img",type=FileStorage, location='files',required=True,help='必须提供一个img的file的表单')

    def post(self):
        args = self.parser.parse_args()

        uploadFile:FileStorage = args.get('img')
        print('上传的文件名:',uploadFile.filename)

        newFileNname = str(uuid.uuid4()).replace('-','')
        newFileNname += "."+uploadFile.filename.split('.')[-1]

        uploadFile.save(os.path.join(settings.MEDIA_DIR,newFileNname))

        return {'msg':'上传成功',
                'path':'/static/uploads/{}'.format(newFileNname)}

# 将资源添加到api对象中，并声明uri
api.add_resource(UserApi,'/user/')
api.add_resource(ImageApi,'/images/')
api.add_resource(MusicApi,'/music/')
api.add_resource(UploadApi,'/upload/')