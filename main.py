from mastodon import Mastodon
import random
import datetime
import time
import re
import logging
import toml



CONF_FILE_PATH = "./duck-hunter.conf.toml"


class Animal:
    def __init__(
            self,
            name,
            bodies,
            noises,
            points = 1,
            shoot_chance = 0.9,
            befriend_chance = 0.9,
            trail="・゜゜・。。・゜゜"):
        self.name = name
        self.body = random.choice(bodies)
        self.noise = random.choice(noises)

        self.points = points
        self.shoot_chance = shoot_chance
        self.befriend_chance = befriend_chance
        self.trail = trail

        self.article = 'a'
        for letter in 'aeiouAEIOU':
            if name.startswith(letter):
                self.article = 'an'
                break

        self.shoot_fail_message = (
            "You missed! It's like you weren't even trying. "
            "You can reload and shoot again in 1 minute.")
        self.befriend_fail_message = (
            f"The {self.name} doesn't seem particularly friendly. "
            f"You can get it a drink and try again in 1 minute.")
        
        self.shoot_succeed_message = (
            f"You shot {self.article} {self.name} "
            f"and gained {self.points} points!")
            
        self.befriend_succeed_message = (
            f"You befriended {self.article} {self.name} "
            f"and gained {self.points} points!")


    def show_animal(self):
        return f"{self.trail} {self.body}  {self.noise}"

    def on_shot(self):
        if random.random() < self.shoot_chance:
            return self.shoot_succeed_message, True
        else:
            return self.shoot_fail_message, False

    def on_befriend(self):
        if random.random() < self.befriend_chance:
            return self.befriend_succeed_message, True
        else:
            return self.befriend_fail_message, False


class Duck(Animal):
    def __init__(self):
        super().__init__(
            "duck",
            ("\_o<", "\_ö<", "\_ø<", "\_ó<"),
            ("QUACK!", "FLAP FLAP FLAP", "quack!", "quonk!"),
            befriend_chance = 0
        )


class Goose(Animal):
    def __init__(self):
        super().__init__(
            "goose",
            ("\_O<", "\_0< ", "\_Ö<", "\_Ø<", "\_Ó<"),
            ("HONK!", "FLAP FLOP FLIP", "honk!", "hjonk!"),
            points=2,
            befriend_chance=0.5
        )
        


class Elephant(Animal):
    def __init__(self):
        super().__init__(
            "elephant",
            ("m°ᒑ°",),
            ("PVVVVT!", "STOMP STOMP STOMP", "pffft!", "phfnnn!"), 
            points = 10,
            befriend_chance = 0.5,
            shoot_chance = 0
        )
        
        self.befriend_fail_message = (
            f"The {self.name} seems to have more important tasks at hand, "
            f"and pays you little attention.")

        self.shoot_fail_message = (
            "Shooting such a wise and noble animal would be a wickedness. "
            "You lower your rifle in shame.")


class Alex(Animal):
    def __init__(self):
        super().__init__(
            "Alex",  # it's me!
            ("\o/",),
            (
                "help! i'm trapped in a game!", 
                "what am i doing here?",
                "it's me, the dev! trans rights!", 
                "it's me, the dev! free palestine!"
            ),
            points = 30,
            shoot_chance = 1,
            befriend_chance = 1
        )
        self.points = 30

        self.shoot_succeed_message = (
            f"Really? You're shooting me? The developer of this game? "
            f"Fine, take your {self.points} points and leave.")

        self.befriend_succeed_message = (
            f"You want to be friends with... me? "
            f"Some guy with nothing better to do than code a "
            f"duck hunting game for Mastodon? Wow... thanks :) "
            f"Here, take {self.points} points!")


def get_animal():
    return random.choices(
        (Duck(), Goose(), Elephant(), Alex()),
        weights=[100, 10, 5, 1]
    )[0]  # choices() returns a list of size k=1

def send_animal(m, config):  # TODO: this long function is a code smell
    chosen_animal = get_animal()
    logging.debug(f"{chosen_animal.name} is the chosen animal")

    id = m.status_post(chosen_animal.show_animal())['id']
    logging.info(f"Sent {chosen_animal.name} successfully")

    me = m.me()['acct']

    # list of Toots that already failed to shoot/befriend -- exclude them from checking
    failed_attempts = []
    # dict of users that have failed, and the time at which they'll be able to try again.
    user_timeouts = {}

    # now we wait for a reply
    while True:
        time.sleep(config['api']['check_intervals']['replies'])  # avoid rate limiting
        check_rate_limit(m)
        replies = m.status_context(id)['descendants']

        winning_reply = None
        winning_reply_action = None

        for this_reply in replies:
            # make sure it's not a reply by ourselves
            if this_reply['account']['acct'] == me:
                continue

            # make sure it's not an already-failed reply
            if this_reply['id'] in failed_attempts:
                logging.debug(f"ignored a previously-failed attempt")
                continue

            # make sure user isn't timed out based on a previous failed reply
            if this_reply['account']['acct'] in user_timeouts:
                timeout_end = user_timeouts[this_reply['account']['acct']]
                if timeout_end > this_reply['created_at']:
                    logging.debug(
                        f"user {this_reply['account']['acct']} is still in "
                        f"timeout and their latest reply has been discarded")
                    failed_attempts.append(this_reply['id'])
                    continue

            # determine action and remove non-action replies
            this_reply_content = re.sub('<[^<]+?>', '', this_reply['content'])\
                                 .lower()\
                                 .strip('!')\
                                 .strip('@duckhunter ')
            if this_reply_content in config['gameplay']['replies']['shoot']:
                this_action = 'shoot'
            elif this_reply_content in config['gameplay']['replies']['befriend']:
                this_action = 'befriend'
            else:
                failed_attempts.append(this_reply['id'])
                continue

            # now we know it's valid, check it's the EARLIEST reply
            # compare to existing choice to see if it's sooner
            if winning_reply is None or this_reply['created_at'] < winning_reply['created_at']:
                winning_reply = this_reply
                winning_reply_action = this_action

        if winning_reply:  # we have a valid reply! yay!
            logging.debug(
                f"winning reply found: {winning_reply_action} the "
                f"{chosen_animal.name} by {winning_reply['account']['acct']}")
            match winning_reply_action:
                case 'shoot':
                    response, action_success = chosen_animal.on_shot()
                case 'befriend':
                    response, action_success = chosen_animal.on_befriend()

            # API CALL - post the response -- regardless of whether it succeeded or not
            m.status_reply(winning_reply, response)

            if action_success:
                logging.info(f"{winning_reply['account']['acct']} SUCCEEDED")
                break  # TODO: add points system
            else:  # they failed, so we need to prevent them from trying again on this animal for 10 seconds.
                logging.info(f"{winning_reply['account']['acct']} FAILED")
                failed_attempts.append(winning_reply['id'])
                user_timeouts[winning_reply['account']['acct']] = winning_reply['created_at'] + datetime.timedelta(seconds=60)


def check_rate_limit(m):
    logging.debug(
        f"rate limiting: {m.ratelimit_remaining} remaining of {m.ratelimit_limit}. "
        f"reset at {m.ratelimit_reset}")


def __main__():
    with open(CONF_FILE_PATH) as conf_file:
        config = toml.load(conf_file)

    logging.basicConfig(filename='duck-hunter.log', level=logging.DEBUG, filemode='w',
                        format='%(asctime)s // %(levelname)s // %(message)s')
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)  # this module creates logging spam
    m = Mastodon(access_token=config['api']['authentication']['secrets_path'])

    logging.info("initialised")
    check_rate_limit(m)

    while True:
        try:
            time.sleep(random.randint(
                config['gameplay']['send_intervals']['minimum'], 
                config['gameplay']['send_intervals']['maximum']
                ))
            send_animal(m, config)
        except KeyboardInterrupt as e:
            logging.info("recieved KeyboardInterrupt, goodbye!")
            break
        except Exception as e:
            logging.exception(e)


if __name__ == '__main__':
    __main__()
