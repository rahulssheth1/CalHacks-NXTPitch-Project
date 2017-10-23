# import itertools
# import turtle
# import random

# def inRange(low, high, theList):
# 	if len(theList) == 0:
# 		return []
# 	head = []
# 	if theList[0] >= low and theList[0] <= high:
# 		head = [theList[0]]
# 	return head + inRange(low, high, theList[1:])

# def draw():
# 	window = turtle.Screen()
# 	window.bgcolor("black")

# 	t = turtle.Turtle()
# 	t.color("red")

# 	size = 0.4

# 	t.pensize(size)
# 	t.speed(0)

# 	colors = ['red',
# 			  'green',
# 			  'blue',
# 			  'yellow',
# 			  'purple',
# 			  'gray',
# 			  'pink',
# 			  'brown',]

# 	i = 1
# 	count = 1
# 	while True:
# 		count += 1
# 		t.color(random.choice(colors))
# 		x = i ** 2
# 		i += 0.05
# 		t.forward(x)
# 		t.right(89)

# 		if count % 10 == 0:
# 			size += 0.1
# 		t.pensize(size)

# def main():
# 	# print inRange(5, 16, [1, 45, 13, 7, 16, 12, 55])
# 	draw()

# if __name__ == "__main__":
# 	draw()

from flask import Flask, url_for, jsonify, request
app = Flask(__name__)

@app.route('/')
def api_root():
    return 'Welcome'

@app.route('/articles')
def api_articles():
    return 'List of ' + url_for('api_articles')

@app.route('/articles/<articleid>')
def api_article(articleid):
    return 'You are reading ' + articleid

@app.route('/hello', methods = ['GET'])
def api_hello():
	if 'number' in request.args:
		data = { 'hello' : 'world',
			 	 'number' : request.args['number'] }
	else:
		data = { 'hello' : 'world',
			 	 'number' : 3 }

	resp = jsonify(data)
	resp.status_code = 200

	return resp

if __name__ == '__main__':
    app.run()






