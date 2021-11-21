char c;
 
void setup() 
{
     Serial.begin(9600);
     Serial.println("Serial started at 9600");
 
     Serial1.begin(9600);  
     Serial.println("BTserial started at 9600");
}
 
void loop() 
{
 
    if (Serial.available() > 0) 
    {
       c = Serial.read();
       Serial1.write(c);
    }
 
 
    if (Serial1.available() > 0) 
    {
       c = Serial1.read();
       Serial.write(c);
    }
}
