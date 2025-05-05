import random

class Player:
    def __init__(self, name):
        self.name = name
        self.role = None
        self.is_alive = True
        self.chat_log = []

    def assign_role(self, role):
        self.role = role
        self.chat_log = []
        self.is_alive = True

    def vote(self, alive_players):
        print(f"\n{self.name}님의 투표 차례입니다.")
        print("투표 대상:")
        for idx, p in enumerate(alive_players):
            print(f"{idx}. {p.name}")
        while True:
            try:
                target_idx = int(input("투표할 플레이어 번호를 입력하세요: "))
                if 0 <= target_idx < len(alive_players):
                    target = alive_players[target_idx]
                    if target.name != target.is_alive:
                        return target
                    else:
                        print("사망자입니다. 다시 선택하세요.")
            except:
                pass
            print("잘못된 입력입니다. 다시 시도하세요.")

    def speak(self):
        return f"{self.name}님이 발언합니다."

    def listen(self, event_type, actor, message, metadata=None):
        log_entry = {
            "event": event_type,
            "actor": actor,
            "message": message,
            "metadata": metadata or {}
        }
        self.chat_log.append(log_entry)

    def __str__(self):
        return f"{self.name} - {'Alive' if self.is_alive else 'Dead'} - {self.role if not self.is_alive else '???'}"

class Game:
    def __init__(self, player_names):
        self.players = [Player(name) for name in player_names]
        self.day_count = 1

    def assign_roles(self):
        roles = ['mafia'] * 1 + ['citizen'] * 4
        random.shuffle(roles)
        for player, role in zip(self.players, roles):
            player.assign_role(role)
        print("\n[모든 플레이어의 역할이 랜덤으로 배정되었습니다.]")

    def get_alive_players(self):
        return [p for p in self.players if p.is_alive]

    def get_mafias(self):
        return [p for p in self.get_alive_players() if p.role == 'mafia']

    def get_citizens(self):
        return [p for p in self.get_alive_players() if p.role == 'citizen']

    def run_day(self):
        print(f"\n☀️ 낮 {self.day_count}이 되었습니다. 토론을 시작합니다.")
        alive_players = self.get_alive_players()
        for p in alive_players:
            p.listen("start_day", "system", f"낮 {self.day_count}이 시작되었습니다.", {"day": self.day_count})

        print(f"\n누구에게 말을 시킬까요?")
        print("생존자:")
        for idx, p in enumerate(alive_players):
            print(f"{idx}. {p.name}")

        while True:
            try:
                target_idx = input("말할 사람의 번호를 입력하세요 (토론을 멈추려면 q를 입력하세요): ")
                if target_idx == "q":
                    print("토론을 종료합니다.")
                    break
                target_idx = int(target_idx)
                if 0 <= target_idx < len(alive_players):
                    message = alive_players[target_idx].speak()
                    for p in alive_players:
                        p.listen("chat", "alive_players[target_idx].name", "message", "message")
                    print(f"\n{alive_players[target_idx].name}님 : {message}")
                else :
                    print("\n잘못된 번호입니다. 다시 입력하세요.")

            except:
                pass
                print("\n잘못된 입력입니다. 다시 시도하세요.")

        votes = {}

        for player in alive_players:
            target = player.vote(alive_players)
            votes[target] = votes.get(target, 0) + 1
            for p in alive_players:
                p.listen("vote", player.name, f"{player.name} 님이 {target.name}에게 투표했습니다.", {"voted_for": target.name})

        # 최다득표자 찾기
        max_votes = max(votes.values())
        candidates = [p for p, v in votes.items() if v == max_votes]

        if len(candidates) > 1:
            print("\n⚠️ 동률이 발생하여 아무도 처형되지 않습니다.")
            for p in alive_players:
                p.listen("execute", "system", "동률 발생으로 처형이 무효되었습니다.")
        else:
            target = candidates[0]
            target.is_alive = False
            print(f"\n🪦 {target.name} 님이 처형되었습니다.")
            for p in self.get_alive_players():
                p.listen("execute", "system", f"{target.name} 님이 처형되었습니다.", {"executed": target.name})

    def run_night(self):
        mafias = self.get_mafias()
        if not mafias:
            return

        print("\n🌙 밤이 되었습니다. 마피아는 시민 중 한 명을 선택해 제거하세요.")
        for p in self.get_alive_players():
            p.listen("start_night", "system", "밤이 시작되었습니다.", {"day": self.day_count})

        alive_players = self.get_alive_players()
        citizens = [p for p in alive_players if p.role != 'mafia']

        if not citizens:
            return

        mafia = mafias[0]  # 한 명 마피아만 있다고 가정
        print(f"\n{mafia.name} 님의 선택 차례입니다.")
        for idx, p in enumerate(citizens):
            print(f"{idx}. {p.name}")

        while True:
            try:
                target_idx = int(input("죽일 시민의 번호를 입력하세요: "))
                if 0 <= target_idx < len(citizens):
                    target = citizens[target_idx]
                    target.is_alive = False
                    print(f"\n💀 밤사이 {target.name} 님이 살해당했습니다.")
                    for p in self.get_alive_players():
                        p.listen("kill", mafia.name, f"{target.name} 님이 밤에 사망했습니다.", {"target": target.name})
                    break
                else:
                    print("잘못된 번호입니다.")
            except:
                print("입력이 잘못되었습니다.")

    def check_winner(self):
        mafias = self.get_mafias()
        citizens = self.get_citizens()

        if not mafias:
            print("\n🎉 시민 팀이 승리했습니다!")
            return True
        elif len(mafias) >= len(citizens):
            print("\n🩸 마피아 팀이 승리했습니다!")
            return True
        return False

    def show_status(self):
        print("\n📋 현재 생존자 상태:")
        for p in self.players:
            print(f" - {p}")

    def start_game(self):
        print("=== 마피아 게임을 시작합니다 ===")
        self.assign_roles()

        while True:
            self.show_status()
            self.run_day()
            if self.check_winner():
                break
            self.run_night()
            if self.check_winner():
                break
            self.day_count += 1

# ===== 게임 시작 =====
if __name__ == "__main__":
    names = ["Alice", "Bob", "Charlie", "Dana", "Eve"]
    game = Game(names)
    game.start_game()
