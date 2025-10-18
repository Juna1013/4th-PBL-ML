from machine import Pin, PWM
import time

# 左モーター
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
left_fwd = PWM(Pin(LEFT_FWD_PIN))
left_rev = PWM(Pin(LEFT_REV_PIN))
left_fwd.freq(1000)
left_rev.freq(1000)

# 右モーター
RIGHT_FWD_PIN = 3
RIGHT_REV_PIN = 2
right_fwd = PWM(Pin(RIGHT_FWD_PIN))
right_rev = PWM(Pin(RIGHT_REV_PIN))
right_fwd.freq(1000)
right_rev.freq(1000)

# モーター単体テスト関数
def test_motor(fwd_pwm, rev_pwm, name="Motor"):
    # 前進
    rev_pwm.duty_u16(0)
    fwd_pwm.duty_u16(40000)
    time.sleep(2)

    # 後退
    fwd_pwm.duty_u16(0)
    rev_pwm.duty_u16(40000)
    time.sleep(2)

    # 停止
    fwd_pwm.duty_u16(0)
    rev_pwm.duty_u16(0)
    print(f"==== {name} 停止 ====")
    time.sleep(1)

# 実行
test_motor(left_fwd, left_rev, "左モーター")
test_motor(right_fwd, right_rev, "右モーター")
