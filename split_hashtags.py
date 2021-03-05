# from nltk.corpus import words

# word_dictionary = list(set(words.words()))
word_dictionary = []
word_dictionary.append("Barda")
word_dictionary.append("Armenian")
word_dictionary.append("Armenia")
word_dictionary.append("Kills")
word_dictionary.append("Aggression")
word_dictionary.append("Stop")
word_dictionary.append("Children")
word_dictionary.append("Terror")
word_dictionary.append("Karabakh")
word_dictionary.append("Azerbaijan")
word_dictionary.extend(["For", "War", "Crimes", "armenian", "stop", "terrorism", "Stay", "Strong", "Ganja", "City", "pray", "civilians",
						"Child", "Killer", "Dont", "Be", "Blind", "Open", "Your", "Eyes", "Believe", "Occupation", "voice", "genocide", "Long",
						"Live", "war", "crimes", "2020", "Smerch", "Terrorism", "Azerbaijani", "WAKE", "UP", "armenia", "armenian", "occupation",
						"aggression", "Ganja", "barda", "Pray", "US", "UK", "Kills", "Unicef", "baby", "Pashinyan", "Tartar", "Armen",
						"city", "Khojaly", "Attacking", "Kills", "killer", "Lies", "Vandalism", "CRIMES", "WAR", "karabakh", "Aliyev", "Artsakh",
						"Nagorno", 'aggressor', "occupiers", "open", "eyes", "world", "Gandja", "France", "Shame", "On", "You", "Today",
						"Human", "Rights", "Fascism", "Is", "let", "children", "die", 'not', 'is', 'france', "Terrorisim",
						"United", "Nations", 'UNICEF', 'unicef', "Nikol", "Attacks", "Civilians", "for", "Genocide", "Justice", "For", "Never", "Forget"])

# for alphabet in "bcdefghjklmnopqrstuvwxyz" + "bcdefghjklmnopqrstuvwxyz".upper():
# 	word_dictionary.remove(alphabet)

def split_hashtag_to_words_all_possibilities(hashtag):
	all_possibilities = []
	
	split_posibility = [hashtag[:i] in word_dictionary for i in reversed(range(len(hashtag)+1))]
	possible_split_positions = [i for i, x in enumerate(split_posibility) if x == True]
	
	for split_pos in possible_split_positions:
		split_words = []
		word_1, word_2 = hashtag[:len(hashtag)-split_pos], hashtag[len(hashtag)-split_pos:]
		
		if word_2 in word_dictionary:
			split_words.append(word_1)
			split_words.append(word_2)
			all_possibilities.append(split_words)

			another_round = split_hashtag_to_words_all_possibilities(word_2)
				
			if len(another_round) > 0:
				all_possibilities = all_possibilities + [[a1] + a2 for a1, a2, in zip([word_1]*len(another_round), another_round)]
		else:
			another_round = split_hashtag_to_words_all_possibilities(word_2)
			
			if len(another_round) > 0:
				all_possibilities = all_possibilities + [[a1] + a2 for a1, a2, in zip([word_1]*len(another_round), another_round)]

	return all_possibilities


# if __name__ == "__main__":
# 	print(split_hashtag_to_words_all_possibilities("StopArmenianTerror"))