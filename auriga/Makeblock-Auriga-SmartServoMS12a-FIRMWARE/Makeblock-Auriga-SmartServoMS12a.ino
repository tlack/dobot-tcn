/**
	
	Makeblock Auriga firmware to provide convenient serial interface
	
*/
#include <SoftwareSerial.h>
#include <Wire.h>
#include "MeAuriga.h"

// CONFIG:
#define MAXSERVOS 10
#define MOVESPEED 200
#define RETURNSPEED 100
#define TWEAKNESS 45
// gyro is buggy for me
#define GYRO 0

#define TXRX_TICKS       10
#define UPD_TICKS        50
#define SUMMARY_TICKS    10000
#define TWEAK_TICKS      0

// when tweaking with unity, all motors must be done with goal tasks before tweaking
// otherwise, a motor (joint) will tweak whenever it is done, independent of others
#define TWEAK_WITH_UNITY 1

// start tweaking when system boots
#define TWEAK_AT_BOOT    0

// after issuing a movement goal, should the joints return to staring position?
#define RETURN_HOME      0

// HELPERS:
#define P Serial.print
#define PN Serial.println
#define FOR_LIVE_SERVOS(x) for (int (x) = 1; (x) <= MAXSERVOS && LIVE[(x)]; (x)++)

// GLOBALS:
MeSmartServo smartservo(PORT5);   //UART2 is on port 5
#if GYRO
MeGyro gyro;
#endif

long loopTime = 0;
#define MAXSERVOSP MAXSERVOS+1
int LIVE[MAXSERVOSP] = {0};
int BUSY[MAXSERVOSP] = {0};
int ANG[MAXSERVOSP] = {0};
int VOLT[MAXSERVOSP] = {0};
int TEMP[MAXSERVOSP] = {0};
int CURRENT[MAXSERVOSP] = {0};
int STARTANG[MAXSERVOSP] = {0};
int TWEAKING[MAXSERVOSP] = {0};
int X, Y, Z = 0;

// find occurs of y in x and place into *buf (maxbuf entries maximum)
int where(String x, char y, int* buf, int maxbuf) {
  int nm = 0; // num matches
  for (int i = 0; i < x.length(); i++) {
    if (x[i] == y) {
      *buf = i;
      buf++;
      maxbuf--;
      nm++;
      if (maxbuf < 0) break;
    }
  }
  return nm;
}

void dbg5(int servo, char* str, int* arg, int* arg2, int* arg3, int* arg4, int* arg5) {
  P(str); P(" "); P(String(servo)); P(" ");

  if (arg) {
    P(String(*arg));
    P(" ");
  }
  if (arg2) {
    P(String(*arg2));
    P(" ");
  }
  if (arg3) {
    P(String(*arg3));
    P(" ");
  }
  if (arg4) {
    P(String(*arg4));
    P(" ");
  }
  if (arg5) {
    P(String(*arg5));
    P(" ");
  }

  PN("");
}
void dbg4(int servo, char* str, int* arg, int* arg2, int* arg3, int* arg4) {
  dbg5(servo, str, arg, arg2, arg3, arg4, NULL);
}
void dbg3(int servo, char* str, int* arg, int* arg2, int* arg3) {
  dbg5(servo, str, arg, arg2, arg3, NULL, NULL);
}
void dbg2(int servo, char* str, int* arg, int* arg2) {
  dbg5(servo, str, arg, arg2, NULL, NULL, NULL);
}
void dbg(int servo, char* str, int* arg) {
  dbg5(servo, str, arg, NULL, NULL, NULL, NULL);
}

int randint(int n) {
  int r = rand() % n + 1;
  return r;
}

void upd(int servo) {
  int OA = ANG[servo];
  ANG[servo] = smartservo.getAngleRequest(servo);
  VOLT[servo] = smartservo.getVoltageRequest(servo);
  CURRENT[servo] = smartservo.getCurrentRequest(servo);
  TEMP[servo] = smartservo.getTempRequest(servo);
  int diff = ANG[servo] - OA;
  if (diff < 0) diff = diff * -1;
  smartservo.setRGBLed(servo, diff * 10, 0, 0);
#if GYRO
  gyro.update();
  X = gyro.getAngleX(); Y = gyro.getAngleY(); Z = gyro.getAngleZ();
#endif
}

void setup()
{
  Serial.begin(115200);
  PN("BOOT");
#if GYRO
  gyro.begin();
#endif
  smartservo.begin(115200);
  delay(10);
  PN("ASSIGN");
  smartservo.assignDevIdRequest();
  delay(40);
  for (int i = 1; i <= MAXSERVOS; i++) {
    if (smartservo.handSharke(i)) {
      upd(i);
      // after upd() at bootup, sometimes get weird values
      delay(2);
      upd(i);
      smartservo.setRGBLed(i, 255, 255, 255);
      STARTANG[i] = ANG[i];
      LIVE[i] = 1;
    } else {
      LIVE[i] = 0;
    }
  }
  summarize();
#if TWEAK_AT_BOOT
  for (int i = 1; i <= MAXSERVOS; i++) {
    if (LIVE[i]) tweak(i);
  }
#endif
  loopTime = millis();
}

void return_cb(uint8_t servo) {
  dbg(servo, "PH", NULL);
  smartservo.setRGBLed(servo, 0, 0, 255);
  smartservo.moveTo(servo, STARTANG[servo], randint(RETURNSPEED), move_cb);
}

void move_cb(uint8_t servo) {
  BUSY[servo] = 0;
  dbg(servo, "P2", NULL);
  smartservo.setRGBLed(servo, 255, 255, 255);
  if (TWEAKING[servo]) tweak(servo);
}

void tweak(int i) {
  if (BUSY[i]) {
    P("BUSY ");
    PN(String(i));
  }
  else {
    BUSY[i] = 1;
    int luck = millis() % 2 == 0;
    int newang = STARTANG[i] + (luck ? TWEAKNESS : (-1 * TWEAKNESS));
    dbg(i, "T1", &newang);
    TWEAKING[i] = 1;
    smartservo.setRGBLed(i, 0, 255, 0);
    smartservo.moveTo(i, newang, randint(MOVESPEED), RETURN_HOME ? return_cb : move_cb);
  }
}

void summarize() {
  int max_servo = 0;
  P("J ");
  FOR_LIVE_SERVOS(servo) {
    // dbg4(servo, "J", &ANG[servo], &VOLT[servo], &CURRENT[servo], &TEMP[servo]);
    P(String(servo));
    P(" ");
    P(String(ANG[servo]));
    P(" ");
    max_servo = servo > max_servo ? servo : max_servo;
  }

#if GYRO
  P("X ");
  P(String(X));
  P(" Y ");
  P(String(Y));
  P(" Z ");
  P(String(Z));
#endif
  PN("");
}

void cmd_get(String cmd) {
  summarize();
}

void cmd_put(String cmd) {
  int tmp[20] = {0};
  int nm = where(cmd, ' ', tmp, sizeof(tmp));
  if (nm == 0 || tmp[0] == 0) {
    P("! ERR - use P [0-360] [0-360]");
    return;
  }
  P("P1 ");
  for (int i = 0; i < nm; i++) {
    int word1 = tmp[i];
    int word2 = i == nm - 1 ? cmd.length() - 1 : tmp[i + 1];
    String argS = cmd.substring(word1, word2);
    P(argS);
    P(" ");
    int arg = argS.toInt();
    // P(String(arg));
    int servo = i + 1;
    smartservo.moveTo(servo, arg, MOVESPEED, move_cb);
  }
  PN("");
}

void cmd_joint(String cmd) {
  int tmp[20] = {0};
  int nm = where(cmd, ' ', tmp, sizeof(tmp));
  if (nm < 2) {
    P("! ERR - use J [joint] [0-360]");
    return;
  }
  String js = cmd.substring(tmp[0] + 1, tmp[1]);
  String ps = cmd.substring(tmp[1] + 1, nm == 3 ? tmp[2] : cmd.length());
  int j = js.toInt();
  if (!LIVE[j]) {
    P("! ERR - joint is not live");
    return;
  }
  int p = ps.toInt();
  P("P1 "); PN(ps);
  int speed = MOVESPEED;
  if (nm == 3) {
    String ss = cmd.substring(tmp[2] + 1, cmd.length());
    speed = ss.toInt();
  }
  smartservo.moveTo(j, p, speed, move_cb);
}

void cmd_tweak(String cmd) {
  int tmp[20] = {0};
  int nm = where(cmd, ' ', tmp, sizeof(tmp));
  if (nm != 1 || tmp[0] == 0) {
    P("! ERR - use T [servo]");
    return;
  }
  String servoS = cmd.substring(tmp[0] + 1, cmd.length());
  int servo = servoS.toInt();
  if (TWEAKING[servo]) {
    TWEAKING[servo] = 0;
    return;
  }
  tweak(servo);
}

void parse_cmd(String cmd) {
  P("CMD "); PN(cmd);
  if (!cmd.length()) return;
  if (cmd[0] == 'G') cmd_get(cmd);
  if (cmd[0] == 'P') cmd_put(cmd);
  if (cmd[0] == 'J') cmd_joint(cmd);
  if (cmd[0] == 'T') cmd_tweak(cmd);
}

void txrx() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    parse_cmd(cmd);
  }
}

void loop()
{
  int last_txrx, last_upd = 0, last_summary = 0, last_tweak = 0;
  int n_servos = 2;
  while (1) {
    int t = millis();
    if (Serial.available()) {
      txrx();
      last_txrx = t;
    }
    if (UPD_TICKS && t - last_upd > UPD_TICKS) {
      FOR_LIVE_SERVOS(servo) {
        upd(servo);
      }
      last_upd = t;
    }
    if (SUMMARY_TICKS && t - last_summary > SUMMARY_TICKS) {
      summarize();
      last_summary = t;
    }
    if (TWEAK_TICKS && t - last_tweak > TWEAK_TICKS) {
      if (TWEAK_WITH_UNITY)
        FOR_LIVE_SERVOS(servo) {
        if (BUSY[servo]) return;
      }
      FOR_LIVE_SERVOS(servo) {
        tweak(servo);
      }
    }
  }
}
