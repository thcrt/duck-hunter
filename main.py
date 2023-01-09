from mastodon import Mastodon
import random
from datetime import datetime
import time
import re

SHOOT_REPLIES = ("bang", )
BEFRIEND_REPLIES = ("befriend", "bef")

class Animal:
    
    def __init__(
            self, 
            name, 
            bodies, 
            noises):
        self.name = name
        self.body = random.choice(bodies)
        self.noise = random.choice(noises)

        self.points = 1
        self.shoot_chance = 0.9
        self.befriend_chance = 0.9
        self.trail = "・゜゜・。。・゜゜"

        self.shoot_fail_message = "You missed! It's like you weren't even trying. You can reload and shoot again in ten seconds."
        self.befriend_fail_message = f"The {self.name} doesn't seem particularly friendly. You can get it a drink and try again in ten seconds."

        self.article = 'a'
        for letter in 'aeiouAEIOU':
            if name.startswith(letter):
                self.article = 'an'
                break

    def show_animal(self):
        return f"{self.tail} {self.body}  {self.noise}"
    
    def on_shot(self):
        if random.random() < self.shoot_chance:
            return f"You shot {self.article} {self.name} and gained {self.points} points!", True
        else:
            return self.shoot_fail_message, False

    def on_befriend(self):
        if random.random() < self.shoot_chance:
            return f"You befriended {self.article} {self.name} and gained {self.points} points!", True
        else:
            return self.befriend_fail_message, False


class Duck(Animal):
    def __init__(self):
        super().__init__(
            "duck",
            ("\_o<", "\_ö<", "\_ø<", "\_ó<"),
            ("QUACK!", "FLAP FLAP FLAP", "quack!", "quonk!")
        )
        self.befriend_chance = 0.95


class Goose(Animal):
    def __init__(self):
        super().__init__(
            "goose",
            ("\_O<", "\_0< ", "\_Ö<", "\_Ø<", "\_Ó<"),
            ("HONK!", "FLAP FLOP FLIP", "honk!", "hjonk!"),
        )
        self.points = 2
        self.befriend_chance = 0.5

class Elephant(Animal):
    def __init__(self):
        super().__init__(
            "elephant",
            ("m°ᒑ°",),
            ("PVVVVT!", "STOMP STOMP STOMP", "pffft!", "phfnnn!"),
        )
        self.points = 10
        self.befriend_fail_message = f"The {self.name} seems to have more important tasks at hand, and pays you little attention."
    
    def on_shot(self):
        return "Shooting such a wise and noble animal would be a wickedness. You lower your rifle in shame.", False



class Alex(Animal):
    def __init__(self):
        super().__init__(
            "Alex",  # it's me!
            ("\o/",),
            ("help! i'm trapped in a game!", "what am i doing here?", "it's me, the dev! trans rights!", "it's me, the dev! free palestine!"),
        )
        self.points = 30
    
    def on_shot(self):
        return f"Really? You're shooting me? The developer of this game? Fine, take your {self.points} points and leave.", True
    
    def on_befriend(self):
        return f"You want to be friends with... me? Some guy with nothing better to do than code a duck hunting game for Mastodon? Wow... thanks :) Here, take {self.points} points!", True



def get_animal():
    i = random.randint(1, 1000) / 10  # get between 1 and 100 with .1 accuracy
    if i <= 95:  # 95% chance
        return Duck()
    elif 95 < i <= 99.5:  # 3% chance
        return Goose()
    elif 99.5 < i <= 99.9 :  # 0.4% chance
        return Elephant()
    else: # 0.1% chance
        return Alex()

        

def send_animal(m):
    chosen_animal = get_animal()
    id = m.status_post(chosen_animal.show_animal())['id']  # post toot, and get its id

    failed_attempts = []  # list of Toots that already failed to shoot/befriend -- exclude them from checking
    user_timeouts = {}  # dict of users that have failed, and the time at which they'll be able to try again.

    # now we wait for a reply
    while True:
        time.sleep(1)  # avoid rate limiting
        replies = m.status_context(id)['descendants']

        earliest_valid_reply = None
        earliest_valid_reply_time = None

        for reply in replies:

            # TODO: make sure it's not an already-failed reply or in the timeout


            reply_time = reply['created_at']
            reply_content = re.sub('<[^<]+?>', '', reply['content']).lower().strip('!')  # remove capitals and exclamations, as well as the HTML tags
            
            if reply_content in SHOOT_REPLIES:
                action = 'shoot'
            elif reply_content in BEFRIEND_REPLIES:
                action = 'befriend'
            else:
                next
            
            if earliest_valid_reply_time is None or reply_time < earliest_valid_reply_time:  # compare to existing choice to seee if it's sooner
                earliest_valid_reply = reply
                earliest_valid_reply_time = reply_time
        
        if earliest_valid_reply:  # we have a valid reply! yay!
            match action:
                case 'shoot': 
                    response, action_success = chosen_animal.on_shot()
                case 'befriend':
                    response, action_success = chosen_animal.on_befriend()

            m.status_reply(earliest_valid_reply, response)  # post the response -- regardless of whether it succeeded or not

            if action_success:
                break  # TODO: add points system
            else:  # they failed, so we need to prevent them from trying again on this animal for 10 seconds.
                failed_attempts.append(earliest_valid_reply)
                user_timeouts[earliest_valid_reply['account']['id']] = earliest_valid_reply['created_at'] + datetime.timedelta(seconds=10)
      

m = Mastodon(access_token="clientcred.secret", api_base_url="https://botsin.space")
send_animal(m)