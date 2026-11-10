#include <Arduino_GFX_Library.h>
#include <Wire.h>
#include <math.h>

Arduino_DataBus *bus = new Arduino_RPiPicoSPI(16, 17, 18, 19, -1, spi0);
Arduino_GFX *gfx = new Arduino_GC9A01(bus, 20, 0, true);
const uint8_t MPU = 0x68;

#define RGB(r,g,b) ((uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)))
const int BTN[3] = {2, 3, 6};
const int BUZZER = 7;
const int MOTOR = 8;

const float MOTOR_ON = 0.45;
const float MOTOR_OFF = 0.30;

const int CX = 120, CY = 120;
const int RSCREEN = 116;
const int CELL = 12;                 // character cell size
const int GRIDN = 20;                // 20x20 grid of cells (240/12)
const int N = 64;

float win[N]; int wi = 0;
float emaJerk = 0, emaGyro = 0, dynPrev = 0;
float out[6] = {0,0,0,0,0,0};
float held[6] = {0,0,0,0,0,0};
bool holding = false;
bool wasAbove = false;
unsigned long lastPeak = 0;
float ivals[4] = {0,0,0,0}; int ivi = 0, ivCount = 0;
bool lastBtn[3] = {false,false,false};

// character ramp: sparse/light to dense/heavy
const char RAMP[] = { ' ', '.', ':', '-', '+', '*', 'o', 'O', '#', '#' };
const int RAMPN = 10;

// remember what character is currently in each cell, so we only redraw changes
char cellNow[GRIDN][GRIDN];

const char* LAB[6] = {"FLOW","BRST","TENS","RHTM","DRFT","RECV"};

float clamp01(float x){ return x < 0 ? 0 : (x > 1 ? 1 : x); }

void readIMU(float &dyn, float &gdps) {
  Wire.beginTransmission(MPU); Wire.write(0x3B); Wire.endTransmission(false);
  Wire.requestFrom(MPU, (uint8_t)14);
  uint8_t b[14]; for (int i=0;i<14;i++) b[i]=Wire.read();
  int16_t ax=(b[0]<<8)|b[1], ay=(b[2]<<8)|b[3], az=(b[4]<<8)|b[5];
  int16_t gx=(b[8]<<8)|b[9], gy=(b[10]<<8)|b[11], gz=(b[12]<<8)|b[13];
  float fx=ax/16384.0,fy=ay/16384.0,fz=az/16384.0;
  dyn = fabs(sqrt(fx*fx+fy*fy+fz*fz)-1.0);
  gdps = sqrt((float)gx*gx+(float)gy*gy+(float)gz*gz)/131.0;
}

int regionAt(int px, int py) {
  float a = atan2(py - CY, px - CX);
  float d = a + PI/2;
  if (d < 0) d += 2*PI;
  int r = (int)(d / (PI/3)) % 6;
  return r;
}

void setup() {
  Serial.begin(115200);
  gfx->begin();
  gfx->fillScreen(RGB565_WHITE);
  Wire.setSDA(4); Wire.setSCL(5); Wire.begin(); Wire.setClock(400000);
  Wire.beginTransmission(MPU); Wire.write(0x6B); Wire.write(0x00); Wire.endTransmission();
  for (int i=0;i<N;i++) win[i]=0;
  for (int i=0;i<3;i++) pinMode(BTN[i], INPUT_PULLUP);
  pinMode(BUZZER, OUTPUT);
  pinMode(MOTOR, OUTPUT);
  digitalWrite(MOTOR, LOW);
  for (int y=0;y<GRIDN;y++) for (int x=0;x<GRIDN;x++) cellNow[y][x] = 0;
  gfx->setTextSize(1);
  delay(100);
}

// draw the stable character field, only updating cells that change
void drawField() {
  gfx->setTextColor(RGB565_BLACK, RGB565_WHITE);
  for (int gy = 0; gy < GRIDN; gy++) {
    for (int gx = 0; gx < GRIDN; gx++) {
      int px = gx*CELL + 6;
      int py = gy*CELL + 6;
      int dx = px + 3 - CX, dy = py + 3 - CY;
      if (dx*dx + dy*dy > RSCREEN*RSCREEN) { cellNow[gy][gx] = 0; continue; }
      int reg = regionAt(px+3, py+3);
      float v = holding ? held[reg] : out[reg];
      // density rises smoothly with value; steady, not random
      float rr = sqrtf((float)(dx*dx + dy*dy)) / RSCREEN;   // 0 centre .. 1 edge
      float level = clamp01(v * 1.15 - rr * 0.35);          // fuller near centre
      int idx = (int)(level * (RAMPN - 1) + 0.5);
      if (idx < 0) idx = 0; if (idx >= RAMPN) idx = RAMPN-1;
      char c = RAMP[idx];
      if (c != cellNow[gy][gx]) {
        // clear the cell then draw the new character
        gfx->fillRect(px, py, CELL, CELL, RGB565_WHITE);
        if (c != ' ') { gfx->setCursor(px, py); gfx->print(c); }
        cellNow[gy][gx] = c;
      }
    }
  }
}

// draw the six region labels once, near the rim, so it's clear what's measured
void drawLabels() {
  gfx->setTextColor(RGB565_BLACK, RGB565_WHITE);
  for (int i=0;i<6;i++){
    float a = -PI/2 + i*PI/3 + PI/6;   // centre of each wedge
    int lx = CX + (int)(96*cos(a)) - 11;
    int ly = CY + (int)(96*sin(a)) - 3;
    gfx->setCursor(lx, ly);
    gfx->print(LAB[i]);
  }
}

void loop() {
  float dyn, gdps; readIMU(dyn, gdps);
  win[wi]=dyn; wi=(wi+1)%N;
  float sum=0,sumsq=0,mx=0;
  for (int i=0;i<N;i++){ sum+=win[i]; sumsq+=win[i]*win[i]; if(win[i]>mx)mx=win[i]; }
  float mean=sum/N, var=sumsq/N-mean*mean; if(var<0)var=0;
  float jerk=fabs(dyn-dynPrev); dynPrev=dyn; emaJerk+=(jerk-emaJerk)*0.2;
  float gnorm=clamp01(gdps/250.0); emaGyro+=(gnorm-emaGyro)*0.1;

  float thr=mean+0.04; unsigned long now=millis();
  if (dyn>thr && !wasAbove){ wasAbove=true; float iv=now-lastPeak; lastPeak=now;
    if(iv>150&&iv<1200){ ivals[ivi]=iv; ivi=(ivi+1)%4; if(ivCount<4)ivCount++; } }
  else if (dyn<thr-0.02) wasAbove=false;
  float rhythm=0;
  if (ivCount>=3 && (now-lastPeak)<1500){
    float is=0; for(int i=0;i<ivCount;i++)is+=ivals[i]; float im=is/ivCount;
    float iv2=0; for(int i=0;i<ivCount;i++){float d=ivals[i]-im;iv2+=d*d;}
    float cv=(im>0)?sqrt(iv2/ivCount)/im:1; rhythm=clamp01(1-cv*1.5);
  }

  float raw[6];
  raw[0] = clamp01((mean - 0.03) * 14.0) * (1.0 - clamp01(emaJerk * 4.0)) * (1.0 - clamp01(var * 20.0));
  raw[1] = clamp01((var - 0.015) * 7.0) * clamp01(emaJerk * 2.5);
  raw[2] = clamp01((mx - 0.35) * 1.6) * clamp01((mean - 0.04) * 8.0) * (1.0 - clamp01(emaJerk * 1.8));
  raw[3] = rhythm * clamp01((mean - 0.12) * 8.0) * (1.0 - clamp01((var - 0.08) * 8.0));
  raw[4] = clamp01(emaGyro * 1.6) * (1.0 - clamp01(mx * 0.8));
  raw[5] = clamp01(1.0 - fmax(mean * 6.0, fmax(emaGyro * 2.0, var * 15.0)));

  const float A[6]={0.15,0.5,0.12,0.1,0.08,0.12};
  for (int i=0;i<6;i++) out[i]+=(raw[i]-out[i])*A[i];

  drawField();
  drawLabels();

  float disp[6];
  for (int i=0;i<6;i++) disp[i] = holding ? held[i] : out[i];
  Serial.print(disp[0],3); Serial.print(',');
  Serial.print(disp[1],3); Serial.print(',');
  Serial.print(disp[2],3); Serial.print(',');
  Serial.print(disp[3],3); Serial.print(',');
  Serial.print(disp[4],3); Serial.print(',');
  Serial.println(disp[5],3);

  for (int i=0;i<3;i++){
    bool p = (digitalRead(BTN[i])==LOW);
    if (p && !lastBtn[i]) {
      if (i==0) {
        for (int k=0;k<6;k++) held[k]=out[k];
        holding = true;
        tone(BUZZER, 880, 120);
        digitalWrite(MOTOR, HIGH); delay(140); digitalWrite(MOTOR, LOW);
      } else if (i==1) {
        holding = false;
        tone(BUZZER, 587, 140);
      } else {
        float s0 = holding?held[0]:out[0];
        float s1 = holding?held[1]:out[1];
        float s2 = holding?held[2]:out[2];
        float inten = clamp01(0.4f*s1 + 0.3f*s2 + 0.3f*s0);
        int ms = 90 + (int)(inten*320);
        tone(BUZZER, 660, ms);
        digitalWrite(MOTOR, HIGH); delay(ms); digitalWrite(MOTOR, LOW);
      }
    }
    lastBtn[i] = p;
  }

  static bool buzzedOnce = false;
  if (!holding) {
    if (out[1] > MOTOR_ON && !buzzedOnce) { digitalWrite(MOTOR, HIGH); buzzedOnce = true; }
    if (out[1] < MOTOR_OFF) { digitalWrite(MOTOR, LOW); buzzedOnce = false; }
  } else buzzedOnce = false;

  delay(20);
}