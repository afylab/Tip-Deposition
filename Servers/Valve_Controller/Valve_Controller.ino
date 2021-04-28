String m = "";
int Controller[] = {2,3,4,5,6,7};
int valvestat[] = {0,0,0};

void setup() {
 int i;
 for(i = 0;i<6;i++){
   pinMode(Controller[i], OUTPUT);
   digitalWrite(Controller[i], LOW);
 }
   Serial.begin(9600);
}

void loop() { 
  if (Serial.available()){
    char input;
    while (input != 'r'){
      if (Serial.available()){
         input = Serial.read();
         if (input != 'r'){
           m += input;
         }
         else if (input = 'r'){
           valve();
         }
         else{
           Serial.print("Invalid Entry.");
      }
    }
  }
}
}

void valve(){
  if(m.startsWith("i")){
    Serial.print("Valve and Relay Control\r\n");
  }  
  else if (m.startsWith("o") && m.endsWith("t")){
    digitalWrite(14, HIGH);
    valvestat[0] = 1;
    Serial.print("Turbo Valve Open\r\n");
  }
  else if (m.startsWith("c") && m.endsWith("t")){
    digitalWrite(14, LOW);
    valvestat[0] = 0;
    Serial.print("Turbo Valve Closed\r\n");
  }  
  else if (m.startsWith("o") && m.endsWith("c")){
    digitalWrite(16, HIGH);
    valvestat[1] = 1;
    Serial.print("Chamber Valve Open\r\n");
  }
  else if (m.startsWith("c") && m.endsWith("c")){
    digitalWrite(16, LOW);
    valvestat[1] = 0;
    Serial.print("Chamber Valve Closed\r\n");
  }  
  else if (m.startsWith("o") && m.endsWith("g")){
    digitalWrite(15, HIGH);
    valvestat[2] = 1;
    Serial.print("Gate Valve Open\r\n");
  }
  else if (m.startsWith("c") && m.endsWith("g")){
    digitalWrite(15, LOW);
    valvestat[2] = 0;
    Serial.print("Gate Valve Closed\r\n");
  }  
   else if (m.startsWith("t") && m.endsWith("p")){
    digitalWrite(3, HIGH);
    Serial.print("Turbo Turned On\r\n");
  }
  else if (m.startsWith("t") && m.endsWith("s")){
    digitalWrite(3, LOW);
    Serial.print("Turbo Turned Off\r\n");
  }  
    else if (m.startsWith("s") && m.endsWith("p")){
    digitalWrite(4, HIGH);
    Serial.print("Scroll Pump On\r\n");
  }
  else if (m.startsWith("s") && m.endsWith("s")){
    digitalWrite(4, LOW);
    Serial.print("Scroll Pump Off\r\n");
  } 
  m = "";
      
  }  
