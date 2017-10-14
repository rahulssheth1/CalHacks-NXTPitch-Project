import httplib
import urllib
import urllib2
import base64
import json
import re
import subprocess
import urllib2
import ATD
import collections
import requests
import os
import subprocess
import unirest
from watson_developer_cloud import ToneAnalyzerV3, PersonalityInsightsV3, SpeechToTextV1
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.layout import LAParams
from cStringIO import StringIO
from flask import Flask, render_template
app = Flask(__name__)

#######################################
## Analytic Modules
#######################################

# Return a score of how positive some text is with 
# 100 being positive and 0 being negative
def analyze_sentiment(text):
	headers = {'Ocp-Apim-Subscription-Key': '26772e6ba9004813ad25898296a076b9'}
	conn = httplib.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
	documents = { 'documents': [
		{ 'id': '1', 'language': 'en', 'text': text }
	]}

	body = json.dumps(documents)
	conn.request("POST", '/text/analytics/v2.0/sentiment', body, headers)
	response = conn.getresponse()
	output_string = str(response.read())
	score = re.search(r'(score)[^,]+', output_string).group(0).replace('"', '')

	arr = score.split(':')

	return int(float(arr[1]) * 100) / 1

# Return the prevailing emotion within an image
def get_main_emotion_from_image():

	command = "ffmpeg -i new.mov -vcodec png -ss 2 -vframes 1 -an -f rawvideo video.png"
	subprocess.call(command, shell=True)

	response = unirest.post("https://eyeris-emovu1.p.mashape.com/api/image/",
		headers={
			"X-Mashape-Key": "XgcJhfwDAfmshV4zdaKvqAMaaYf7p1m4gTHjsnirknCVhFzWJr"
		},
		params={
			"imageFile": open("video.png", mode="r")
		}
	)

	data = response.body

	dataset = data["FaceAnalysisResults"][0]["EmotionResult"]

	try:
		del dataset["Computed"]
	except KeyError:
		pass

	max = 0
	for i in dataset:
		if float(dataset[i]) > max:
			max = float(dataset[i])
			val = i

	os.remove('video.png')

	return val

# Return biggest personality, largest contributor, largest need
def get_personality_from_text(input):
	personality_insights = PersonalityInsightsV3(version='2016-10-20',
												 username='f3b3071b-81fa-4461-a4be-6d76cb30ba03',
												 password='5k5gWTCGzXWn')

	profile = personality_insights.profile(input, raw_scores=True,
										   consumption_preferences=True)
	max = 0
	personality = dict()
	personality['name'] = ''
	for i in profile['personality']:
		if float(i['raw_score']) > max:
			max = float(i['raw_score'])
			personality = i

	max = 0
	trait = dict()
	trait['name'] = ''
	for i in personality['children']:
		if float(i['raw_score']) > max:
			max = float(i['raw_score'])
			trait = i

	max = 0
	need = dict()
	need['name'] = ''
	for i in profile['needs']:
		if float(i['raw_score']) > max:
			max = float(i['raw_score'])
			need = i

	return [personality['name'], trait['name'], need['name']]

# Return strongest emotional tone, language tone, social tone
def get_tone_from_text(text):
	tone_analyzer = ToneAnalyzerV3(username='211b4aa5-20de-420a-b455-55ff7fc3633b',
								   password='01rS1c50h3p8',
								   version='2016-05-19')

	tones = tone_analyzer.tone(text=text)

	# Emotion Tone
	max = 0
	etone = dict()
	etone['tone_name'] = ""
	for i in tones['document_tone']['tone_categories'][0]['tones']:
		if float(i['score']) > max:
			max = float(i['score'])
			etone = i

	# Language Tone
	max = 0
	ltone = dict()
	ltone['tone_name'] = ""
	for i in tones['document_tone']['tone_categories'][1]['tones']:
		if float(i['score']) > max:
			max = float(i['score'])
			ltone = i

	# Social Tone
	max = 0
	stone = dict()
	stone['tone_name'] = ""
	for i in tones['document_tone']['tone_categories'][2]['tones']:
		if float(i['score']) > max:
			max = float(i['score'])
			stone = i

	return [etone['tone_name'], ltone['tone_name'], stone['tone_name']] 

# Return top three key phrases
def get_key_phrases(text):
	headers = {'Ocp-Apim-Subscription-Key': '26772e6ba9004813ad25898296a076b9'}
	conn = httplib.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
	documents = { 'documents': [
		{ 'id': '1', 'language': 'en', 'text': text }
	]}

	body = json.dumps(documents)
	conn.request("POST", '/text/analytics/v2.0/keyPhrases', body, headers)
	response = conn.getresponse()
	output_string = str(response.read())
	words = re.search(r'(keyPhrases)[^\]]+', output_string).group(0).replace('[', '').replace('"', '').replace(':', ',')

	phrases = words.split(',')
	phrases.append('')
	phrases.append('')
	return [phrases[1], phrases[2], phrases[3]]

def is_subseq(x, y):
	it = iter(y)
	return all(any(c == ch for c in it) for ch in x)

# Return number of grammar and word choice mistakes
def check_grammar(text):
	ATD.setDefaultKey("5k5gWTCGzXWn")
	metrics = ATD.stats(text)
	spell_count = 0
	grammar_count = 0
	for i in [str(m) for m in metrics]:
		if is_subseq('spell', i):
			spell_count += int(re.search(r'[\d]+', i).group(0))
		elif is_subseq('grammar', i):
			grammar_count += int(re.search(r'[\d]+', i).group(0))

	return [grammar_count, spell_count]

# Return 5 most used words within some text with elem 0 being most used
def get_top_five_used_words(text):
	counts = collections.Counter(text.split())
	return [elem for elem, _ in counts.most_common(5)]

#######################################
## Controller Modules
#######################################

# Return string representing spoken text
def convert_audio_to_text(file):
	speech_to_text = SpeechToTextV1(
		username='7639ec5e-4a13-4d16-8760-00bb6cb3596e',
		password='ZcBkCmbqUZZH',
		x_watson_learning_opt_out=False)

	with open(file, 'rb') as audio:
		output = speech_to_text.recognize(
				audio, content_type='audio/flac', timestamps=True,
				word_confidence=True)

	text = output['results'][0]['alternatives'][0]['transcript']
	return text

# Return string representing text contents of pdf
def extract_text_from_pdf(filename):
	fp = open(filename, 'rb')
	rsrcmgr = PDFResourceManager()
	retstr = StringIO()
	codec = 'utf-8'
	laparams = LAParams()
	device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

	# Create a PDF interpreter object.
	interpreter = PDFPageInterpreter(rsrcmgr, device)

	# Process each page contained in the document.
	for page in PDFPage.get_pages(fp):
		interpreter.process_page(page)
		data =  retstr.getvalue()

	clean_data = "\n".join([line for line in data.split('\n') if line.strip() != ''])

	list_data = clean_data.split('\n')

	filtered = list()
	for line in list_data[:-1]:
		newline = line.replace('-', '').replace('\t', '').replace('\xe2\x80\xa2', '').strip()
		filtered.append(newline)

	return "\n".join(filtered)

def controller(url, type):
	if type == '1':
		command = "ffmpeg -i new.mov -ab 160k -ac 2 -ar 44100 -vn audio.flac"
		subprocess.call(command, shell=True)

		file_text = convert_audio_to_text("audio.flac")

		output = dict()

		# Emotional Analysis
		output["positivity"] = analyze_sentiment(file_text)
		output["expression"] = get_main_emotion_from_image()

		tones = get_tone_from_text(file_text)

		output["toneE"] = tones[0]
		output["toneL"] = tones[1]
		output["toneS"] = tones[2]

		# Highlighted Content
		phrases = get_key_phrases(file_text)

		output["phrases1"] = phrases[0]
		output["phrases2"] = phrases[1]
		output["phrases3"] = phrases[2]

		words = get_top_five_used_words(file_text)

		output["word1"] = words[0]
		output["word2"] = words[1]
		output["word3"] = words[2]
		output["word4"] = words[3]
		output["word5"] = words[4]
		
		# Professionalism
		grammar = check_grammar(file_text)

		output["grammar"] = grammar[0]
		output["words"] = grammar[1]

		os.remove("audio.flac")

		return output
	elif type == '2':
		response = urllib2.urlopen(url)

		temp_file = open("document.pdf", "wb")
		temp_file.write(response.read())
		temp_file.close()

		file_text = extract_text_from_pdf("document.pdf")

		output = dict()

		# Emotional Analysis
		output["positivity"] = analyze_sentiment(file_text)

		expressions = get_personality_from_text(file_text)

		output["expression1"] = expressions[0]
		output["expression2"] = expressions[1]
		output["expression3"] = expressions[2]

		tones = get_tone_from_text(file_text)

		output["toneE"] = tones[0]
		output["toneL"] = tones[1]
		output["toneS"] = tones[2]

		# Highlighted Content
		phrases = get_key_phrases(file_text)

		output["phrases1"] = phrases[0]
		output["phrases2"] = phrases[1]
		output["phrases3"] = phrases[2]

		words = get_top_five_used_words(file_text)

		output["word1"] = words[0]
		output["word2"] = words[1]
		output["word3"] = words[2]
		output["word4"] = words[3]
		output["word5"] = words[4]
		
		# Professionalism
		grammar = check_grammar(file_text)

		output["grammar"] = grammar[0]
		output["words"] = grammar[1]

		os.remove("document.pdf")

		return output

@app.route("/")
def template_test():
	output = controller("new.mov", "1")
	print output
	return render_template('template.html', positivity=output["positivity"],
						   expression=output["expression"], emotional=output["toneE"],
						   language=output['toneL'], social=output['toneS'],
						   one=output['phrases1'], two=output['phrases2'],
						   three=output['phrases3'], onew=output['word1'],
						   twow=output['word2'], threew=output['word3'],
						   fourw=output['word4'], fivew=output['word5'],
						   grammar=output['grammar'], word=output['words'])

if __name__ == '__main__':
	ON_HEROKU = os.environ.get('ON_HEROKU')

	if ON_HEROKU:
   		# get the heroku port
    		serve_port = int(os.environ.get('PORT', 17995))  # as per OP comments default is 17995
	else:
    		serve_port = 3000
	app.run(debug=True, port=serve_port)

