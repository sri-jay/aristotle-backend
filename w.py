import pprint,json

questions  = {
	'NUMBER_OF_QUESTIONS' : '2',
	'QUESTIONS' : {
		'1' : {
			'STATEMENT' : "Hi!, I'm uler, without the E. Who am I named after?",
			'OPTION_A' : "Leonhard Euler",
			'OPTION_B' : "Leonardo Da Vinci",
			'OPTION_C' : "Galilio Galilei",
			'OPTION_D' : "Nicolaus Copernicus"
		},
		'2' : {
			'STATEMENT' : "Did you see that?",
			'OPTION_A' : "YES!",
			'OPTION_B' : "NO"
		}
	}
}

printer = pprint.PrettyPrinter(indent = 4)
printer.pprint(json.dumps(questions))
