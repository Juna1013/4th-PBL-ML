// センサーとモーターのピン定義
const int SENSOR_LEFT = A0;
const int SENSOR_CENTER = A1;
const int SENSOR_RIGHT = A2;

const int MOTOR_LEFT_PWM = 9;  // 左モーター速度制御 (PWM)
const int MOTOR_RIGHT_PWM = 10; // 右モーター速度制御 (PWM)
const int MOTOR_LEFT_DIR = 8;  // 左モーター方向制御 (HIGH/LOW)
const int MOTOR_RIGHT_DIR = 11; // 右モーター方向制御 (HIGH/LOW)

// 速度設定
const int BASE_SPEED = 150; // 基本的な直進速度 (0-255)
const int TURN_ADJUST = 50; // 旋回時の速度調整量

// センサー閾値 (光の反射によってラインを検知する値。要調整)
// 例えば、ラインが黒でセンサーが白い部分で高値を出す場合、低い値がラインを示す
const int LINE_THRESHOLD = 500;

void setup() {
  // ピンモード設定
  pinMode(SENSOR_LEFT, INPUT);
  pinMode(SENSOR_CENTER, INPUT);
  pinMode(SENSOR_RIGHT, INPUT);

  pinMode(MOTOR_LEFT_PWM, OUTPUT);
  pinMode(MOTOR_RIGHT_PWM, OUTPUT);
  pinMode(MOTOR_LEFT_DIR, OUTPUT);
  pinMode(MOTOR_RIGHT_DIR, OUTPUT);

  // モーターの方向を常に前進に設定 (一般的なライントレース)
  digitalWrite(MOTOR_LEFT_DIR, HIGH);
  digitalWrite(MOTOR_RIGHT_DIR, HIGH);

  Serial.begin(9600); // デバッグ用
}

void loop() {
  // センサー値の読み取り
  bool left_on_line = analogRead(SENSOR_LEFT) < LINE_THRESHOLD;
  bool center_on_line = analogRead(SENSOR_CENTER) < LINE_THRESHOLD;
  bool right_on_line = analogRead(SENSOR_RIGHT) < LINE_THRESHOLD;

  // デバッグ出力
  Serial.print("L:"); Serial.print(left_on_line);
  Serial.print(" C:"); Serial.print(center_on_line);
  Serial.print(" R:"); Serial.print(right_on_line);
  Serial.println();

  // 制御ロジック
  if (center_on_line) {
    // 中央センサーがライン上: 直進
    setMotors(BASE_SPEED, BASE_SPEED);
  } else if (left_on_line) {
    // 左センサーがライン上: 右に旋回 (右モーターを速く)
    setMotors(BASE_SPEED - TURN_ADJUST, BASE_SPEED + TURN_ADJUST);
  } else if (right_on_line) {
    // 右センサーがライン上: 左に旋回 (左モーターを速く)
    setMotors(BASE_SPEED + TURN_ADJUST, BASE_SPEED - TURN_ADJUST);
  } else {
    // ラインを見失った場合: 一旦停止または後退/探索など
    // ここでは停止
    setMotors(0, 0);
  }
}

// モーター速度設定関数 (前進のみ考慮)
void setMotors(int leftSpeed, int rightSpeed) {
  // 速度が負にならないように調整 (PWMは0-255)
  leftSpeed = constrain(leftSpeed, 0, 255);
  rightSpeed = constrain(rightSpeed, 0, 255);

  analogWrite(MOTOR_LEFT_PWM, leftSpeed);
  analogWrite(MOTOR_RIGHT_PWM, rightSpeed);
}
