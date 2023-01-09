from mastodon import Mastodon
import random
import time



class Animal:
    tail = "・゜゜・。。・゜゜"
    def __init__(self, name, bodies, noises, points):
        self.name = name
        self.body = random.choice(bodies)
        self.noise = random.choice(noises)
        self.points = points
    
    def show_animal(self):
        return f"{self.tail} {self.body}  {self.noise}"



def get_animal():
    i = random.randint(1, 1000) / 10  # get between 1 and 100 with .1 accuracy
    if i <= 95:  # 95% chance
        return Animal(
            "duck",
            ("\_o<", "\_ö<", "\_ø<", "\_ó<"),
            ("QUACK!", "FLAP FLAP FLAP", "quack!", "quonk!"),
            1
        )
    elif 95 > i <= 99.5:  # 3% chance
        return Animal(
            "goose",
            ("\_O<", "\_0< ", "\_Ö<", "\_Ø<", "\_Ó<"),
            ("HONK!", "FLAP FLOP FLIP", "honk!", "hjonk!"),
            3
        )
    else:  # 0.5% chance
        return Animal(
            "elephant",
            ("m°ᒑ°",),
            ("PVVVVT!", "STOMP STOMP STOMP", "pffft!", "phfnnn!"),
            10
        )



def send_animal():
    chosen_animal = get_animal()
    id = m.status_post(chosen_animal.show_animal())['id']  # post toot, and get its id

    # now we wait for a reply
    while True:
        time.sleep(15)  # avoid rate limiting
        


m = Mastodon(access_token="clientcred.secret", api_base_url="https://botsin.space")
