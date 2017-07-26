from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import re, cgi


from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

from database_setup import Restaurant, Base, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()






class WebServerHandler(BaseHTTPRequestHandler):
    def send_ok_response(self, input, display_headers = True):
        if display_headers:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        message = ""
        message += "<html><body>" + input  + "</body></html>"
        self.wfile.write(message)
        print message
        return


    def get_all_restaurants(self):
        restaurants = session.query(Restaurant).all()
        return restaurants
    def get_restaurant(self, id):
        restaurant = session.query(Restaurant).filter_by(id = id).one()
        return restaurant
    def get_restaurant_html(self, restaurant):
        html = '<div class="restaurant-container">'
        html += '<h3 class="restaurant-heading">' + restaurant.name + '</h3>'
        html += '<a href="/restaurants/' + str(restaurant.id) + '/edit">Edit</a><br/>'
        html += '<a href="/restaurants/' + str(restaurant.id) + '/delete">Delete</a>'
        return html
    def create_html_form(self, entity_type, existing_id=False):
        html = '<form action="" method="post" enctype="multipart/form-data">'
        if existing_id == False:
            html += '<input type="text" name="name" placeholder="Create a new ' + entity_type + '"/>'
            button_label = "Create"
        else:
            existing_id = int(existing_id)
            restaurant = self.get_restaurant(existing_id)
            html += '<input type="text" name="name" placeholder="Edit ' + restaurant.name + '"/>'
            html += '<input type="hidden" name="rename" value="true"/>'
            html += '<input type="hidden" name="id" value="'  + str(existing_id) +'"/>'
            button_label = "Rename"

        html += '<input type="hidden" name="entity_type" value="' + entity_type + '"/>'
        html += '<input type="submit" value="' + button_label  +'"/>'
        html += '</form>'
        return html
    def create_new(self, name, entity_type):
        if entity_type == "restaurant":
            try:
                restaurant = Restaurant(name = name)
                session.add(restaurant)
                session.commit()
                return True
            except:
                session.rollback()
                return False

        if entity_type == "menu_item":
            pass

    def do_GET(self):
	try:
            #find /restaurants/1/
            matches = re.findall(r'(\/)(\d+)(\/)?', self.path)
            if (len(matches) == 1 and len(matches[0]) == 3) :
                match_id = matches[0][1]
            else:
                match_id = ""
	    if self.path.endswith("/new"):
                form = self.create_html_form('restaurant')
                return self.send_ok_response(form);
	    if self.path.endswith("/hello"):
                return self.send_ok_response('Hello')
            if self.path.endswith("/restaurants"):
                return self.send_ok_response('Restaurants')
            if "restaurants/" in self.path:
                if "edit" in self.path:
                    if match_id != "":
                        html = self.create_html_form(entity_type = 'restaurant', existing_id = match_id)
                        return self.send_ok_response(html)
                    else:
                        return self.send_ok_response('Unknown restaurant or menu_item')
                if match_id != "" :
                    restaurant = self.get_restaurant(match_id)
                    html_restaurant = self.get_restaurant_html(restaurant)
                    return self.send_ok_response(html_restaurant)
                else:
                    restaurants = self.get_all_restaurants()
                    message = ""
                    for restaurant in restaurants:
                        message += self.get_restaurant_html(restaurant)

                    return self.send_ok_response(message)


	except IOError:
	    self.send_error(404, 'File Not Found %s' % self.path)

    def do_POST(self):
        try:
            self.send_response(301)
            self.end_headers()

            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                fields=cgi.parse_multipart(self.rfile, pdict)
                renamecontent = fields.get('rename')
                rename = renamecontent[0]
                entity_typecontent = fields.get('entity_type')
                entity_type = entity_typecontent[0]
                entity_id = fields.get('id')[0]
                namecontent = fields.get('name')
                name = namecontent[0]
                if rename == "true":
                    if (entity_type == "restaurant"):
                        restaurant = self.get_restaurant(entity_id)
                        restaurant.name =name
                        session.flush()
                        session.commit()
                        self.send_ok_response(restaurant.name, display_headers = False)
                else:
                    status = self.create_new(name, entity_type)
                    if status:
                        self.send_ok_response('Created successfully');
                    else:
                        self.send_ok_response('Unable to create {} as type {} '.format( name, entity_type))
        except IOError:
            pass


def main():
    try:
	port = 8080
	server = HTTPServer(('', port), WebServerHandler)
	print "Web Server running on port %s" % port
	server.serve_forever()

    except KeyboardInterrupt:
	print " ^C entered, stopping web server...."
	server.socket.close()



if __name__ == '__main__':
    main()
