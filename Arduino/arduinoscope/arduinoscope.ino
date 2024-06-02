#include <SPI.h>

#define MY_SPI_SCK 4000000 //4Mhz MAX frequency for SPI chip recomends 2Mhz
#define MY_SPI_ORDER MSBFIRST         // SPI ORDER
#define MY_SPI_MODE SPI_MODE0  

#define SPICS 10

const uint8_t channelA = 0;
const uint8_t channelB = 2;
const byte commandA = ((0x01 << 7) | (1 << 6) | ((channelA & 0x07) << 3)); // channel number
const byte commandB = ((0x01 << 7) | (1 << 6) | ((channelB & 0x07) << 3)); // channel number


void setup() {
  Serial.begin(2000000);
  while(!Serial);

  //SPI Pins 10 CS ; 11 MOSI ; 12 MISO ; 13 SCK.
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
  digitalWrite(3, HIGH);

  pinMode(SPICS, OUTPUT);
	digitalWrite(SPICS,HIGH);
	SPI.begin();
	SPI.beginTransaction(SPISettings(MY_SPI_SCK, MY_SPI_ORDER, MY_SPI_MODE));

}


volatile byte b0, b1, b2;
volatile uint8_t topval;
volatile uint8_t bottomval;

volatile bool CHAN_A = true; 
volatile bool CHAN_B = false;


void loop() {

  while(1){
    if (Serial.available()){
      volatile uint8_t in = Serial.read();
      //CHAN_A = (channels & 0b1111 == 0b1111);
      //CHAN_B = ((channels & 0b11110000)>>4 == 0b1111);
      if (in > 2){
        CHAN_B = !CHAN_B;
        CHAN_A = CHAN_A ^ CHAN_B;
        
        digitalWrite(3, CHAN_A);
        digitalWrite(4, CHAN_B);

      }
      Serial.flush();
    }

    if (CHAN_A){
      PORTB &= ~(1<<PB2); //port manipulation

      b0 = SPI.transfer(commandA);  //spi command sent and recieve data at the same time
      b1 = SPI.transfer(0x00);
      b2 = SPI.transfer(0x00);

      PORTB |= (1<<PB2);

      topval = ((b0 & 0x01) << 3) | ((b1 & 0xE0) >> 5);
    
      bottomval = ((b1 & 0x1F) << 3)| ((b2 & 0xE0) >> 5);
      //leading bit is zero for channel A
      ///micros() << 6 |

      //Serial.println(topval << 8 | bottomval);
      Serial.write(0xFF);
      Serial.write(topval | 0b00000000);
      Serial.write(bottomval);


    }

    if (CHAN_B){
      PORTB &= ~(1<<PB2);

      b0 = SPI.transfer(commandB);  //spi command sent and recieve data at the same time
      b1 = SPI.transfer(0x00);
      b2 = SPI.transfer(0x00);

      PORTB |= (1<<PB2);

      topval = ((b0 & 0x01) << 3) | ((b1 & 0xE0) >> 5);
    
      bottomval = ((b1 & 0x1F) << 3)| ((b2 & 0xE0) >> 5);
      
      Serial.write(0xFF);
      Serial.write(topval | 0b11110000);
      Serial.write(bottomval);

    }

  }

}




