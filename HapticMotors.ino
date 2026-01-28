int HapPinL = 5;
int HapPinR = 8;
String Mode = "EMPTY";

void setup(){
  pinMode(HapPinL, OUTPUT);
  pinMode(HapPinR, OUTPUT);
}

void loop(){
  if (Mode == "LEFT"){
    digitalWrite(HapPinL, HIGH);
    delay(100);

  
    digitalWrite(HapPinL, LOW);
    delay(100);
    
  }

  else if (Mode == "RIGHT"){
    digitalWrite(HapPinR, HIGH);
    delay(100);

  
    digitalWrite(HapPinR, LOW);
    delay(100);
    
  }

  else if (Mode == "MIDDLE"){
    digitalWrite(HapPinL, HIGH);
    digitalWrite(HapPinR, HIGH);
    delay(100);

  
    digitalWrite(HapPinL, LOW);
    digitalWrite(HapPinR, LOW);
    delay(100);
  }

  

}
