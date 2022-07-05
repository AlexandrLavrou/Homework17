# app.py

from flask import Flask, request
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTX_JSON'] = {'ensure_ascii': False, 'indent': 2}
db = SQLAlchemy(app)

api = Api(app)
movie_ns = api.namespace('movies')


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


###########
##Schemas##
###########


class MovieSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre_id = fields.Int()
    director_id = fields.Int()


class DirectorSchema(Schema):
    id = fields.Int()
    name = fields.Str()


class GenreSchema(Schema):
    id = fields.Int()
    name = fields.Str()


movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)


############
###routes###
############


@movie_ns.route('/')
class MoviesView(Resource):
    def get(self):
        movie_with_genre_and_director = db.session.query(Movie.id, Movie.title, Movie.description,
                                                         Movie.rating, Movie.trailer, Movie.genre_id, Movie.director_id,
                                                         Genre.name.label('genre'),
                                                         Director.name.label('director')).join(Genre).join(Director)
        director_id = request.args.get('director_id')
        genre_id = request.args.get('genre_id')
        if director_id:
            movie_with_genre_and_director = movie_with_genre_and_director.filter(Movie.director_id == director_id)
        if genre_id:
            movie_with_genre_and_director = movie_with_genre_and_director.filter(Movie.genre_id == genre_id)

        movies_list = movie_with_genre_and_director.all()
        return movies_schema.dump(movies_list), 200

    def post(self):
        req_json = request.json
        new_movie = Movie(**req_json)
        with db.session.begin():
            db.session.add(new_movie)
        return "", 201


@movie_ns.route('/<int:mid>')
class MovieView(Resource):
    def get(self, mid: int):
        try:
            movie = Movie.query.get(mid)
            return movie_schema.dump(movie), 200
        except Exception as e:
            return f"{e}", 404

    def patch(self, movie_id: int):
        movie = db.session.query(Movie).get(movie_id)
        if not movie:
            return "Нет такого фильма", 404

        req_json = request.json
        if 'title' in req_json:
            movie.title = req_json['title']
        if 'description' in req_json:
            movie.description = req_json['description']
        if 'rating' in req_json:
            movie.rating = req_json['rating']
        if 'year' in req_json:
            movie.year = req_json['year']
        if 'trailer' in req_json:
            movie.trailer = req_json['trailer']
        if 'genre_id' in req_json:
            movie.genre_id = req_json['genre_id']
        if 'director_id' in req_json:
            movie.director_id = req_json['director_id']
        db.session.add(movie)
        db.session.commit()
        return "", 204

    def put(self, movie_id):
        movie = db.session.query(Movie).get(movie_id)
        if not movie:
            return "", 404
        req_json = request.json

        movie.title = req_json['title']
        movie.description = req_json['description']
        movie.rating = req_json['rating']
        movie.year = req_json['year']
        movie.trailer = req_json['trailer']
        movie.genre_id = req_json['genre_id']
        movie.director_id = req_json['director_id']
        db.session.add(movie)
        db.session.commit()
        return "", 204

    def delete(self, mid):
        try:
            movie = Movie.query.get(mid)
            db.session.delete(movie)
            return "", 204
        except Exception as e:
            return f"{e}", 404


if __name__ == '__main__':
    app.run(debug=True)
