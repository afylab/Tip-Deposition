
String m = "";
String d = "";
int A[] = {3,5,7}; //Pin Order: {Step, Direction, Enable)}, A[] is Shutter Blade and B[] is Tip Rotator
int B[] = {31, 35, 39};
int C = 52;
char rotstat;

void setup(){

  #define MS1 4
  #define MS2 5

int state=LOW;
  pinMode(A[0], OUTPUT);
  pinMode(A[1], OUTPUT);
  pinMode(MS1, OUTPUT);
  pinMode(MS2, OUTPUT);
  pinMode(A[2], OUTPUT);
  pinMode(B[0], OUTPUT);
  pinMode(B[1], OUTPUT);
  pinMode(B[2], OUTPUT);
  pinMode(C, OUTPUT);
  digitalWrite(A[2], LOW);
  digitalWrite(B[2], LOW);
  digitalWrite(C, LOW);
  Serial.begin(9600);
}

void loop(){
  if(Serial.available()){
    char rec; //="";
    String m = "";
    while (rec != 'r'){
      if(Serial.available()){
        rec = Serial.read();
        //Serial.print("m = " + m + "\r\n");
        if(rec != 'r'){
          m += rec;
        }
        else if(rec == 'r'){
          //Serial.print("process m = " + m + "\r\n");
          m.trim(); // Removes any leading or trailing whitespace
          if(m.endsWith("C") || m.endsWith("A")){ 
            Serial.print("turning evaporator shutter\r\n");
            turn(m);
            Serial.print("evaporator has turned\r\n");
            m="";
          }
          else if(m == "i"){
            Serial.print("Stepper Motor Control\r\n");
            m="";
          }
          else if(m == "s"){
            Serial.print("stationary\r\n");
            m="";
          }
          else if(m.startsWith("eo")){
            Serial.print("open effusion cell shutter\r\n");
            open_effusion();
            m="";
          }
          else if(m.startsWith("ec")){
            Serial.print("close effusion cell shutter\r\n");
            close_effusion();
            m="";
          }
          else {
            Serial.print("Invalid entry.\r\n");
            Serial.print("m = " + m + "\r\n");
            m = "";
          }
        }
      }
    }
  }
}

void open_effusion(){
  digitalWrite(C, HIGH);
  Serial.print("m = " + m + "\r\n");
}

void close_effusion(){
  digitalWrite(C, LOW);
  Serial.print("m = " + m + "\r\n");
}

void turn(String m){
  int stp; int dir; float x=0;
  String d = m.substring(1,m.length()-1);
  Serial.print(d);
  String motor = ""; String direct = "";
  char stepper = m.charAt(0);
  if(stepper == 'A'){
    stp = (int)A[0]; dir = (int)A[1]; x = (d.toFloat() * 8) / 1.8;
  }
  else if (stepper == 'B') {
    stp = (int)B[0]; dir = (int)B[1]; x = (d.toFloat() * 8) / 1.8; 
  }
  float y=1;
  if(m.endsWith("C")){digitalWrite(dir, HIGH);}
  else if(m.endsWith("A")){digitalWrite(dir,LOW); }
  for(y= 1; y<x;y++) {
    digitalWrite(stp,HIGH); 
    delay(4);
    digitalWrite(stp,LOW); 
    delay(2);
    if(Serial.available()){
      rotstat = Serial.read();
      if(rotstat == 's'){
        Serial.print("turning\r\n");
      }
    }
  }
  while (Serial.available()){
    Serial.read();
  }
}
