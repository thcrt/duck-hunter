from mastodon import Mastodon
import random
import datetime
import time
import re
import logging


SHOOT_REPLIES = ("bang", )
BEFRIEND_REPLIES = ("befriend", "bef")

SEND_INTERVAL_MIN_SECONDS = 30
SEND_INTERVAL_MAX_SECONDS = 60

CHECK_REPLY_INTERVAL_SECONDS = 10


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

        self.shoot_fail_message = "You missed! It's like you weren't even trying. You can reload and shoot again in 1 minute."
        self.befriend_fail_message = f"The {self.name} doesn't seem particularly friendly. You can get it a drink and try again in 1 minute."

        self.article = 'a'
        for letter in 'aeiouAEIOU':
            if name.startswith(letter):
                self.article = 'an'
                break

    def show_animal(self):
        return f"{self.trail} {self.body}  {self.noise}"

    def on_shot(self):
        if random.random() < self.shoot_chance:
            return f"You shot {self.article} {self.name} and gained {self.points} points!", True
        else:
            return self.shoot_fail_message, False

    def on_befriend(self):
        if random.random() < self.befriend_chance:
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
        self.befriend_chance = 0


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
            ("help! i'm trapped in a game!", "what am i doing here?",
             "it's me, the dev! trans rights!", "it's me, the dev! free palestine!"),
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
    elif 99.5 < i <= 99.9:  # 0.4% chance
        return Elephant()
    else:  # 0.1% chance
        return Alex()


def send_animal(m):
    chosen_animal = get_animal()
    logging.debug(f"{chosen_animal.name} is the chosen animal")

    id = m.status_post(chosen_animal.show_animal())['id']
    logging.info(f"Sent {chosen_animal.name} successfully")

    me = m.me()['acct']

    failed_attempts = []  # list of Toots that already failed to shoot/befriend -- exclude them from checking
    user_timeouts = {}  # dict of users that have failed, and the time at which they'll be able to try again.

    # now we wait for a reply
    while True:
        time.sleep(CHECK_REPLY_INTERVAL_SECONDS)  # avoid rate limiting
        check_rate_limit(m)
        replies = m.status_context(id)['descendants']

        winning_reply = None
        winning_reply_action = None

        for this_reply in replies:
            this_reply_content = re.sub('<[^<]+?>', '', this_reply['content']).lower().strip(
                '!').strip('@duckhunter ')  # remove capitals, exclamations, HTML tags, and @duckhunter
            this_reply_user = this_reply['account']['acct']

            # make sure it's not a reply by ourselves
            if this_reply_user == me:
                logging.debug(f"ignored a reply from this account, {me}")
                continue

            # make sure it's not an already-failed reply
            if this_reply['id'] in failed_attempts:
                logging.debug(f"an attempt by {this_reply_user} has already failed and will not be checked again")
                continue

            # make sure user isn't timed out based on a previous failed reply
            if this_reply_user in user_timeouts:
                timeout_end = user_timeouts[this_reply_user]
                if timeout_end > this_reply['created_at']:
                    logging.debug(f"user {this_reply_user} is still in timeout and their latest reply has been discarded")
                    failed_attempts.append(this_reply['id'])
                    continue
                else:
                    logging.debug(f"user {this_reply_user} has left timeout and their latest reply is valid")

            # determine action and remove non-action replies
            if this_reply_content in SHOOT_REPLIES:
                this_action = 'shoot'
            elif this_reply_content in BEFRIEND_REPLIES:
                this_action = 'befriend'
            else:
                logging.debug(f"reply {this_reply_content} by {this_reply_user} was invalid and has been discarded")
                failed_attempts.append(this_reply['id'])
                continue

            # now we know it's valid, check it's the EARLIEST reply
            # compare to existing choice to see if it's sooner
            if winning_reply is None or this_reply['created_at'] < winning_reply['created_at']:
                winning_reply = this_reply
                winning_reply_action = this_action

        if winning_reply:  # we have a valid reply! yay!
            logging.debug(f"valid reply found: {winning_reply_action} the {chosen_animal.name} by {winning_reply['account']['acct']}")
            match winning_reply_action:
                case 'shoot':
                    response, action_success = chosen_animal.on_shot()
                case 'befriend':
                    response, action_success = chosen_animal.on_befriend()

            # API CALL - post the response -- regardless of whether it succeeded or not
            m.status_reply(winning_reply, response)

            if action_success:
                logging.info(f"action {winning_reply_action} {chosen_animal.name} by {winning_reply['account']['acct']} SUCCEEDED, they were awarded {chosen_animal.points} points")
                break  # TODO: add points system
            else:  # they failed, so we need to prevent them from trying again on this animal for 10 seconds.
                logging.info(f"action {winning_reply_action} {chosen_animal.name} by {winning_reply['account']['acct']} FAILED")
                failed_attempts.append(winning_reply['id'])
                user_timeouts[winning_reply['account']['acct']] = winning_reply['created_at'] + datetime.timedelta(seconds=60)


def check_rate_limit(m):
    logging.debug(f"rate limiting: {m.ratelimit_remaining} remaining of {m.ratelimit_limit}. reset at {m.ratelimit_reset}")


def __main__():
    logging.basicConfig(filename='duck-hunter.log', level=logging.DEBUG, filemode='w', 
                        format='%(asctime)s // %(levelname)s // %(message)s')
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)  # this module creates logging spam
    m = Mastodon(access_token="clientcred.secret")

    logging.info("initialised")
    check_rate_limit(m)

    while True:
        send_animal(m)
        time.sleep(random.randint(SEND_INTERVAL_MIN_SECONDS, SEND_INTERVAL_MAX_SECONDS))


if __name__ == '__main__':
    try:
        __main__()
    except Exception as e:
        logging.exception(e)
