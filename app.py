#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#


import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from sqlalchemy.orm import backref
from sqlalchemy.sql import func
from forms import *
from flask_migrate import Migrate

from models import db, Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db.init_app(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    recent_venues = Venue.query.order_by(db.desc(Venue.id)).limit(10).all()
    recent_artists = Artist.query.order_by(db.desc(Artist.id)).limit(10).all()
    return render_template('pages/home.html', venues = recent_venues, artists = recent_artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    # num_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    venues_grouped_by_state_city = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    for item in venues_grouped_by_state_city:
        a = dict()
        a['city'] = item[0]
        a['state'] = item[1]
        result_venue = db.session.query(Venue.id, Venue.name).filter(Venue.city==a['city']).all()
        venues = []
        for v in result_venue:
            ve = dict()
            ve['id'] = v[0]
            ve['name'] = v[1]
            ve['num_upcoming_shows'] = len(db.session.query(Show.start_time).filter(Show.venue_id==ve['id'], Show.start_time>=func.NOW()).all())
            venues.append(ve)
        a['venues'] = venues
        data.append(a)

    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # search for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  result_venues = Venue.query.filter(Venue.name.ilike("%{}%".format(request.form.get('search_term', '')))).all()
  response={
    "count": len(result_venues),
    "data": []
    }
  for venue in result_venues:
    response["data"].append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(db.session.query(Show.start_time).filter(Show.venue_id==venue.id, Show.start_time>=func.NOW()).all())
      })
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres.split(','),
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": [],
        "upcoming_shows": [],
    }
    #past_shows = Show.query.filter(Show.venue_id==venue_id, Show.start_time<func.NOW())
    past_shows = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id, Show.start_time<func.NOW())
    for show in past_shows:
        data["past_shows"].append({
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })
    #upcoming_shows = Show.query.filter(Show.venue_id==venue_id, Show.start_time>=func.NOW())
    upcoming_shows = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id, Show.start_time>=func.NOW())
    for show in upcoming_shows:
        data["upcoming_shows"].append({
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })
    data["past_shows_count"] = Show.query.filter(Show.venue_id==venue_id, Show.start_time<func.NOW()).count()
    data["upcoming_shows_count"] = Show.query.filter(Show.venue_id==venue_id, Show.start_time>=func.NOW()).count()

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    new_venue = Venue()
    new_venue.name = request.form['name']
    new_venue.city = request.form['city']
    new_venue.state = request.form['state']
    new_venue.address = request.form['address']
    new_venue.phone = request.form['phone']
    new_venue.facebook_link = request.form['facebook_link']
    new_venue.genres = request.form['genres']
    new_venue.website = request.form['website_link']
    new_venue.image_link = request.form['image_link']
    new_venue.seeking_talent = bool(request.form['seeking_talent'])
    new_venue.seeking_description = str(request.form['seeking_description'])

    try:
        db.session.add(new_venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
        db.session.close()

    return redirect(url_for('index'))

#  Delete Venue
#  ----------------------------------------------------------------

@app.route('/venues/<venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    try:
        venue_to_delete = Venue.query.get(venue_id)
        venue_to_delete_name = venue_to_delete.name
        db.session.delete(venue_to_delete)
        db.session.commit()
        flash('Venue ' + venue_to_delete_name + 'with ID: ' + venue_id + ' was successfully deleted!')
    except:
        db.session.rollback()
        flash('please try again. Venue ' + venue_to_delete_name + 'with ID: ' + venue_id + ' could not be deleted.')
    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = list()
  artists = db.session.query(Artist.id, Artist.name).all()
  for artist in artists:
    data.append({
        "id": artist.id,
        "name": artist.name,
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    result_artists = Artist.query.filter(Artist.name.ilike("%{}%".format(request.form.get('search_term', '')))).all()
    response={
        "count": len(result_artists),
        "data": []
        }
    for artist in result_artists:
        response["data"].append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": len(db.session.query(Show.start_time).filter(Show.artist_id==artist.id, Show.start_time>=func.NOW()).all())
        })

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id

    artist = Venue.query.get(artist_id)
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres.split(','),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_talent": artist.seeking_talent,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": [],
        "upcoming_shows": [],
    }
    #past_shows = Show.query.filter(Show.artist_id == artist_id, Show.start_time < func.NOW())
    past_shows = db.session.query(Show).join(Artist).filter(Show.artist_id == artist_id, Show.start_time < func.NOW())
    for show in past_shows:
        data["past_shows"].append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })
    #upcoming_shows = Show.query.filter(Show.artist_id == artist_id, Show.start_time >= func.NOW())
    upcoming_shows = db.session.query(Show).join(Artist).filter(Show.artist_id == artist_id, Show.start_time >= func.NOW())
    for show in upcoming_shows:
        data["upcoming_shows"].append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })
    data["past_shows_count"] = Show.query.filter(Show.artist_id == artist_id, Show.start_time < func.NOW()).count()
    data["upcoming_shows_count"] = Show.query.filter(Show.artist_id == artist_id, Show.start_time >= func.NOW()).count()

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    r_artist = Venue.query.get(artist_id)
    artist = {
        "id": r_artist.id,
        "name": r_artist.name,
        "genres": r_artist.genres.split(','),
        "city": r_artist.city,
        "state": r_artist.state,
        "phone": r_artist.phone,
        "website": r_artist.website,
        "facebook_link": r_artist.facebook_link,
        "seeking_talent": r_artist.seeking_talent,
        "seeking_description": r_artist.seeking_description,
        "image_link": r_artist.image_link,
    }

    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    edit_artist = Artist.query.get(artist_id)
    edit_artist.name = request.form['name']
    edit_artist.city = request.form['city']
    edit_artist.state = request.form['state']
    edit_artist.phone = request.form['phone']
    edit_artist.facebook_link = request.form['facebook_link']
    edit_artist.genres = request.form['genres']
    edit_artist.website = request.form['website_link']
    edit_artist.image_link = request.form['image_link']
    edit_artist.seeking_talent = bool(request.form['seeking_talent'])
    edit_artist.seeking_description = str(request.form['seeking_description'])

    try:
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully edited!')
    except:
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be edited.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
        db.session.close()


    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    r_venue = Venue.query.get(venue_id)
    venue = {
        "id": r_venue.id,
        "name": r_venue.name,
        "genres": r_venue.genres.split(','),
        "address": r_venue.address,
        "city": r_venue.city,
        "state": r_venue.state,
        "phone": r_venue.phone,
        "website": r_venue.website,
        "facebook_link": r_venue.facebook_link,
        "seeking_talent": r_venue.seeking_talent,
        "seeking_description": r_venue.seeking_description,
        "image_link": r_venue.image_link,
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes

    edit_venue = Venue.query.get(venue_id)
    edit_venue.name = request.form['name']
    edit_venue.city = request.form['city']
    edit_venue.state = request.form['state']
    edit_venue.address = request.form['address']
    edit_venue.phone = request.form['phone']
    edit_venue.facebook_link = request.form['facebook_link']
    edit_venue.genres = request.form['genres']
    edit_venue.website = request.form['website_link']
    edit_venue.image_link = request.form['image_link']
    edit_venue.seeking_talent = bool(request.form['seeking_talent'])
    edit_venue.seeking_description = str(request.form['seeking_description'])

    try:
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully edited!')
    except:
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    new_artist = Artist()
    new_artist.name = request.form['name']
    new_artist.city = request.form['city']
    new_artist.state = request.form['state']
    new_artist.phone = request.form['phone']
    new_artist.facebook_link = request.form['facebook_link']
    new_artist.genres = request.form['genres']
    new_artist.website = request.form['website_link']
    new_artist.image_link = request.form['image_link']
    new_artist.seeking_venue = bool(request.form['seeking_venue'])
    new_artist.seeking_description = str(request.form['seeking_description'])

    try:
        db.session.add(new_artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
        db.session.close()

    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    data = list()
    shows = Show.query.all()
    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })

    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    # ensure that the provided ids exist
    if Venue.query.get(request.form['artist_id']) and Venue.query.get(request.form['venue_id']):
        new_show = Show()
        new_show.artist_id = request.form['artist_id']
        new_show.venue_id = request.form['venue_id']
        new_show.start_time = request.form['start_time']

        try:
            db.session.add(new_show)
            db.session.commit()
            # on successful db insert, flash success
            flash('Show was successfully listed!')
        except:
            db.session.rollback()
            # TODO: on unsuccessful db insert, flash an error instead.
            flash('An error occurred. Show could not be listed.')
            # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        finally:
            db.session.close()
    else:
        flash("An error occurred. the provided IDs don't exist, Show could not be listed.")

    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
