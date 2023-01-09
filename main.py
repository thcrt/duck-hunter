from mastodon import Mastodon
import random
import time
import re

VALID_REPLIES = ("bang", "befriend", "bef")

class Animal:
    tail = "・゜゜・。。・゜゜"
    def __init__(self, name, bodies, noises, points):
        self.name = name
        self.body = random.choice(bodies)
        self.noise = random.choice(noises)
        self.points = points

        self.article = 'a'
        for letter in 'aeiouAEIOU':
            if name.startswith(letter):
                self.article = 'an'
                break

    def show_animal(self):
        return f"{self.tail} {self.body}  {self.noise}"
    
    def on_shot(self):
        return f"You shot {self.article} {self.name}!"

    def on_befriend(self):
        return f"You befriended {self.article} {self.name}!"



def get_animal():
    i = random.randint(1, 1000) / 10  # get between 1 and 100 with .1 accuracy
    if i <= 95:  # 95% chance
        return Animal(
            "duck",
            ("\_o<", "\_ö<", "\_ø<", "\_ó<"),
            ("QUACK!", "FLAP FLAP FLAP", "quack!", "quonk!"),
            1
        )
    elif 95 < i <= 99.5:  # 3% chance
        return Animal(
            "goose",
            ("\_O<", "\_0< ", "\_Ö<", "\_Ø<", "\_Ó<"),
            ("HONK!", "FLAP FLOP FLIP", "honk!", "hjonk!"),
            3
        )
    elif 99.5 < i <= 99.9 :  # 0.4% chance
        return Animal(
            "elephant",
            ("m°ᒑ°",),
            ("PVVVVT!", "STOMP STOMP STOMP", "pffft!", "phfnnn!"),
            10
        )
    else: # 0.1% chance
        return Animal(
            "Alex",  # it's me!
            ("\o/",),
            ("help! i'm trapped in a game!", "what am i doing here?", "trans rights!", "free palestine!", "remember to drink water!"),
            30
        )



def get_winning_reply(replies, valid_reply_contents):
    earliest_valid_reply = None
    earliest_valid_reply_time = None

    for reply in replies:
        reply_time = reply['created_at']
        reply_content = re.sub('<[^<]+?>', '', reply['content']).lower().strip('!')  # remove capitals and exclamations, as well as the HTML tags
        if reply_content in valid_reply_contents:  # make sure it's a valid response, like "bang" or "befriend"
            if earliest_valid_reply_time is None or reply_time < earliest_valid_reply_time:  # compare to existing choice to seee if it's sooner
                earliest_valid_reply = reply
                earliest_valid_reply_time = reply_time

    return earliest_valid_reply
        

def send_animal(m):
    chosen_animal = get_animal()
    id = m.status_post(chosen_animal.show_animal())['id']  # post toot, and get its id

    # now we wait for a reply
    while True:
        time.sleep(1)  # avoid rate limiting
        replies = m.status_context(id)['descendants']
        if replies:
            winning_reply = get_winning_reply(replies, VALID_REPLIES)
            if winning_reply:
                m.status_reply(winning_reply, chosen_animal.on_shot())
                return


m = Mastodon(access_token="clientcred.secret", api_base_url="https://botsin.space")
send_animal(m)