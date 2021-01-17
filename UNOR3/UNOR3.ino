#include <Arduino_FreeRTOS.h>

// define two tasks for Blink & AnalogRead
void TaskRunMotors( void *pvParameters );
void TaskReadSerial( void *pvParameters );

void setup() {
  
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  //Serial1.begin(9600);
  
  while (!Serial) {;}

  // Now set up two tasks to run independently.
  xTaskCreate(
    TaskRunMotors
    ,  "RunMotors"   // A name just for humans
    ,  128  // This stack size can be checked & adjusted by reading the Stack Highwater
    ,  NULL
    ,  1  // Priority, with 3 (configMAX_PRIORITIES - 1) being the highest, and 0 being the lowest.
    ,  NULL );

  xTaskCreate(
    TaskReadSerial
    ,  "ReadSerial"
    ,  128  // Stack size
    ,  NULL
    ,  2  // Priority
    ,  NULL );

  // Now the task scheduler, which takes over control of scheduling individual tasks, is automatically started.
}
void loop()
{
  // Empty. Things are done in Tasks.
}

// Global variables
// Motor pins
int ENA = 5; // Left enable
int ENB = 6; // Right enable

int IN1 = 7; // Left Forwards
int IN2 = 8; // Left Backwards
int IN3 = 9; // Right Forwards
int IN4 = 11; // Right Backwards

// Light sensor pins
int LLpin = 2;
int MLpin = 4;
int RLpin = 10;

enum MotorState {
  MOTOR_FORWARDS,
  MOTOR_BACKWARDS,
  MOTOR_STOPPED
};

// Default data is to not be moving
struct MotorData {
  int PWMpin;   //Pin for pwm
  int Fpin;     //Pin to go forwards
  int Bpin;     //Pin to go backwards
  int power = 0;
  MotorState state = MOTOR_STOPPED;
} leftMotor, rightMotor;

enum DriveState {
  DRIVE_FORWARDS,
  DRIVE_BACKWARDS,
  DRIVE_FORWARDS_RIGHT,
  DRIVE_FORWARDS_LEFT,
  DRIVE_BACKWARDS_RIGHT,
  DRIVE_BACKWARDS_LEFT,
  DRIVE_LEFT,
  DRIVE_RIGHT,
  DRIVE_STOPPED
};

class Drive {
  public:
    Drive(MotorData lm, MotorData rm) {
      _lm = lm;
      _rm = rm;
      _rm.PWMpin = ENA;
      _lm.PWMpin = ENB;
    
      _lm.Fpin = IN1;
      _lm.Bpin = IN2;
      _rm.Fpin = IN4;
      _rm.Bpin = IN3;
      pinMode(IN1, OUTPUT);
      pinMode(IN2, OUTPUT);
      pinMode(IN3, OUTPUT);
      pinMode(IN4, OUTPUT);
      setLeftForwards();
      setRightForwards();
    };
    void runDrive() {
      runMotors();
    };
    //Driving forwards or backwards
    // power -255 to 255
    void driveMotors(int power) {
      if(_routineBackup || _routineTurn){
        return;
      }
      if(power > 0){
        _state = DRIVE_FORWARDS;
      } else if(power < 0) {
        _state = DRIVE_BACKWARDS;
        power*=-1;
      } else {
        _state = DRIVE_STOPPED;
      }
      _lm.power = power;
      _rm.power = power;
      Serial.println("runnig");
      _runCount = 10;
    };
    void driveMotors(int power, int runCount) {
      if(_routineTurn || _routineBackup){
        return;
      }
      driveMotors(power);
      _routineBackup = true;
      _runCount = runCount;
    }
    void turnMotors(int power) {
      if(power > 0){
        _state = DRIVE_RIGHT;
      } else if(power < 0) {
        _state = DRIVE_LEFT;
        power*=-1;
      } else {
        _state = DRIVE_STOPPED;
      }
      _lm.power = power;
      _rm.power = power;
      _runCount = 5;
    };
    void turnMotors(int power, int runCount) {
      if(_routineBackup || _routineTurn){
        return;
      }
      turnMotors(power);
      _routineTurn = true;
      _runCount = runCount;
    };
    void stopMotors(){
      _state = DRIVE_STOPPED;
      runMotors();
    };
    void jitterMotors(){
      _jitter = true;
      _lm.power = 150;
      _rm.power = 150;
      _runCount = 100;
    };
    void runRoutine(){
      _routine = true;
    };
    void stopRoutine(){
      _routine = false;
      _routineTurn = false;
      _routineBackup = false;
    };
    bool getRoutine(){
      return _routine;
    };
    bool readLightSensors() {
      if(digitalRead(RLpin) || digitalRead(RLpin) || digitalRead(RLpin)){
        return false;
      }
      return true;
    };
  private:
    float _steerMultiplier;
    MotorData _lm;
    MotorData _rm;
    DriveState _state = DRIVE_STOPPED;
    DriveState _prevState = DRIVE_FORWARDS;
    int _runCount = 0;
    bool _jitter = false;
    bool _routine = false;
    bool _routineTurn = false;
    bool _routineBackup = false;
    // Runs motors at calculated powers, switches direction pins
    void runMotors() {
      if(_runCount > 0){
        if(_jitter){
          if((_runCount / 10) % 2 == 0){
            _state = DRIVE_LEFT;
          } else {
            _state = DRIVE_RIGHT;
          }
        }
        _runCount--;
      } else if(_runCount == 0){
        if(_state != DRIVE_STOPPED){
          _jitter = false;
          _state = DRIVE_STOPPED;
          if(_routineTurn){
            _routineTurn = false;
          }
          if(_routineBackup){
            _routineBackup = false;
            turnMotors(200, 70);
            Serial.println("turn");
          }
        }
      }
      if(_state != _prevState){
        switch(_state){
          case DRIVE_STOPPED:
            Serial.println("stopping");
            _lm.power = 0;
            _rm.power = 0;
            break;
          case DRIVE_BACKWARDS:
            Serial.println("back");
            setLeftBackwards();
            setRightBackwards();
            break;
          case DRIVE_FORWARDS:
            Serial.println("notback");
            setLeftForwards();
            setRightForwards();
            break;
          case DRIVE_LEFT:
            setLeftForwards();
            setRightBackwards();
            break;
          case DRIVE_RIGHT:
            setLeftBackwards();
            setRightForwards();
            break;
          default:
            break;
        }
        _prevState = _state;
      }
      analogWrite(_lm.PWMpin, _lm.power);
      analogWrite(_rm.PWMpin, _rm.power);
      //Serial.println(_runCount);
    };
    void setLeftForwards() {
      digitalWrite(_lm.Bpin, LOW);
      digitalWrite(_lm.Fpin, HIGH);
    };
    void setRightForwards() {
      digitalWrite(_rm.Bpin, LOW);
      digitalWrite(_rm.Fpin, HIGH);
    };
    void setLeftBackwards() {
      digitalWrite(_lm.Fpin, LOW);
      digitalWrite(_lm.Bpin, HIGH);
    };
    void setRightBackwards() {
      digitalWrite(_rm.Fpin, LOW);
      digitalWrite(_rm.Bpin, HIGH);
    };
}d(leftMotor, rightMotor);



void TaskRunMotors(void *pvParameters)  // This is a task.
{
  (void) pvParameters;

  for (;;) // A Task shall never return or exit.
  {
    if(d.getRoutine()){
      if(d.readLightSensors()){
        d.driveMotors(-250, 20);
      } else {
        d.driveMotors(115);
      }
    }
    d.runDrive();
    vTaskDelay(1);
  }
}


void TaskReadSerial(void *pvParameters)  // This is a task.
{
  (void) pvParameters;
  char command[12];
  command[0] = 'n';
  for (;;)
  {
    /*
     * d = drive
     * t = turn 
     * s = stop
     * k = kill
     */
    if(Serial.available()) {
      //While loop to read command
      bool terminated = false;
      int i = 0;
      char c = Serial.read();
      if(c == 'd' || c == 't' || c == 's' || c == 'j' || c == 'r'){
        command[i] = c;
        Serial.println(c);
        while(!terminated) {
          if(Serial.available()) {
            i++;
            command[i] = Serial.read();
            if(command[i] == 'k'){
              terminated = true;
            }
          }
        }
      } else {
        command[i] = 'n';
      }
    }
    if(command[0] != 'n') {
      if(command[0] != 'r'){
        d.stopRoutine();
      }
      Serial.println(command[0]);
      int i = 1;
      char valc[4] = {0, 0, 0, 0};
      int val = 0;
      switch(command[0]) {
        case 's':
          Serial.print("bruh");
          d.stopMotors();
          break;
        case 'd':
          
          while(true) {
            //Serial.print(command[i]);
            if(command[i] == 'k'){
              break;
            }
            
            valc[i-1] = command[i];
            i++;
          }

          val = atoi(valc);

          d.driveMotors(val);
          break;
        case 't':
          while(true) {
            //Serial.print(command[i]);
            if(command[i] == 'k'){
              break;
            }
            
            valc[i-1] = command[i];
            i++;
          }

          val = atoi(valc);

          d.turnMotors(val);
          break;
        case 'j':
          d.jitterMotors();
          break;

        case 'r':
          d.runRoutine();
          break;
          
        default:
          break;
      }
    }
    

    
    vTaskDelay(1);  // one tick delay (15ms) in between reads for stability
  }
}
