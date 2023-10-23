#include <Arduino.h>
#include "pins_arduino.h"
#include <avr/interrupt.h>
#include <avr/power.h>
#include <avr/sleep.h>

#define SHIFT_ROW_3 15
#define SHIFT_ROW_2 14
#define SHIFT_ROW_1 13
#define SHIFT_SSB_ON 11
#define SHIFT_TX_PA 10
#define SHIFT_LNA_ON 9
#define SHIFT_RED_EN 8
#define SHIFT_LED_80 7
#define SHIFT_LED_70 6
#define SHIFT_LED_60 5
#define SHIFT_LED_50 4
#define SHIFT_LED_40 3
#define SHIFT_LED_30 2
#define SHIFT_LED_20 1
#define SHIFT_LED_10 0

// Order is pin 5, pin 6, for shift value 7, 6, 5
#define SWITCH_TX_PA 5
#define SWITCH_SSB_ON 4
#define SWITCH_RX_LNA 3
#define SWITCH_SET_PWR 2
#define SWITCH_SHOW_SWR 0

// Pinout
#define SPI_SCK_PIN 13  // PB5: Connect to PA pin 10, Clock
#define SPI_MOSI_PIN 11 // PB3: Connect to PA pin 9, Data In
#define SPI_SS_PIN 10   // PB2: Connect to PA pin 7, OE_n

#define SHIFT_VALID_PIN 8 // PB0: Connect to PA pin 8, Storage Clock
#define MATRIX_A_PIN 7    // PD7: Connect to PA pin 5, MAT_A
#define MATRIX_B_PIN 6    // PD6: Connect to PA pin 6, MAT_B

#define DA_EN_PIN 5  // Connect to DA ??? via 3.3V voltage divider
#define DA_SWR_PIN 4 // Connect to DA ???

// Globals
volatile uint8_t spi_buffer[2] = {0};
volatile bool spi_pos = 0;
volatile bool message_ready = 0;

volatile uint16_t curShiftState = 0;
volatile uint8_t curSwitchState = 0;

char commandByte = 0;
bool daSwitch = 0;
bool daOverSWR = 0;

void processCommand(char command, char target);

/*
 *  SPI ISR
 *  Fires when SPIF bit is set (i.e. there is data available)
 *  ISR stores the byte available into a buffer.
 */
ISR(SPI_STC_vect)
{
    spi_buffer[spi_pos] = SPDR;

    spi_pos = spi_pos ? 0 : 1;
}

/*
 *  SHIFT_VALID ISR
 *  Fires at any change in state on pin PB0 = pin 8
 *  If rising edge, then the SPI transaction is complete.
 *  Handle switch transitions at this point
 */

ISR(PCINT0_vect) {

    // if ((PINB & (1 << PINB0)) == 1)
    // The valid time is like 100ns which is faster than the Uno can get to the ISR
    if (spi_pos == 0)
    {
        curShiftState = (((uint16_t)spi_buffer[0]) << 8 | spi_buffer[1]);

        message_ready = 1;

        // Set switch col state to match row state
        // col pins are bit 7 = MAT_A, bit 6 = MAT_B
        //Serial.print(curShiftState, HEX);
        //Serial.println(bitRead(curShiftState, SHIFT_ROW_1));
        uint8_t writeValues = 0;
        if (bitRead(curShiftState, SHIFT_ROW_3)) {
            writeValues = (curSwitchState & 0b00110000) << 2;
        } else if (bitRead(curShiftState, SHIFT_ROW_2)) {
            writeValues = (curSwitchState & 0b00001100) << 4;
        } else {
            writeValues = (curSwitchState & 0b00000011) << 6;
        }

        PORTD = (PORTD & 0b00111111) | writeValues;
    }
}

void setup()
{
    // General I/O mapping
    pinMode(SHIFT_VALID_PIN, INPUT);
    pinMode(MATRIX_A_PIN, OUTPUT);
    pinMode(MATRIX_B_PIN, OUTPUT);
    pinMode(DA_EN_PIN, OUTPUT);
    pinMode(DA_SWR_PIN, INPUT);

    // SPI Slave setup based on https://arduino.stackexchange.com/a/89092/10712
    // Enable slave mode, SPI interrupts
    cli();             // disable interrupts
    SPCR |= _BV(SPE);  // Enable SPI
    SPCR |= _BV(SPIE); // Enable interrupts
    // _BV(MSTR) is 0 by default == slave

    // Enable interrupt on "shift valid" rising edge
    // Assuming SHIFT_VALID_PIN is pin 8 = PCINT0
    // Source : https://thewanderingengineer.com/2014/08/11/arduino-pin-change-interrupts/
    PCICR |= _BV(PCIE0);   // turn on port b
    PCMSK0 |= _BV(PCINT0); // turn on pin PB0, which is PCINT0, arduino pin 8
    PCIFR |= _BV(PCIF0);   // Clear outstanding interrupts
    sei();                 // enable interrupts

    power_timer0_disable();
    Serial.begin(115200);
    Serial.println("Toptek Switch Interface");

}

void loop()
{

    // Switch state handling is automatically handled by the ISR
    // In the master loop we just have to poll for new data and serial activity
    if (Serial.available()) {
        char peek = Serial.read();
        Serial.print(peek);

        // First byte recieved is the command, second is target
        if (peek == '\r' || peek == '\n') {
            // noop
        } else if (commandByte == 0) {
            commandByte = peek;
        } else {
            processCommand(commandByte, peek);
            commandByte = 0;
        }

    }

    // Refresh DA values
    digitalWrite(DA_EN_PIN, daSwitch);
    daOverSWR = (DA_SWR_PIN);
}

void processCommand(char command, char target) {
    Serial.println("");
    if (command == 'R') {
        switch(target) {
            case 'A':
                Serial.println(curShiftState, HEX);
                break;
            case 'S': 
                Serial.println(daOverSWR, HEX);
                break;
            case 'W':
                Serial.println(curSwitchState, HEX);
                break;
            case '1':
                Serial.println(bitRead(curSwitchState, SWITCH_SSB_ON), HEX);
                break;
            case '2':
                Serial.println(bitRead(curSwitchState, SWITCH_TX_PA), HEX);
                break;
            case '3':
                Serial.println(bitRead(curSwitchState, SWITCH_SET_PWR), HEX);
                break;
            case '4':
                Serial.println(bitRead(curSwitchState, SWITCH_RX_LNA), HEX);
                break;
            case '5':
                Serial.println(bitRead(curSwitchState, SWITCH_SHOW_SWR), HEX);
                break;
            case '6':
                Serial.println(daSwitch, HEX);
                break;
            default:
                Serial.println("Unhandled statement");
        }
    } else if (command == 'S') {
        switch(target) {
            case '1':
                bitSet(curSwitchState, SWITCH_SSB_ON);
                break;
            case '2':
                bitSet(curSwitchState, SWITCH_TX_PA);
                break;
            case '3':
                bitSet(curSwitchState, SWITCH_SET_PWR);
                break;
            case '4':
                bitSet(curSwitchState, SWITCH_RX_LNA);
                break;
            case '5':
                bitSet(curSwitchState, SWITCH_SHOW_SWR);
                break;
            case '6': 
                daSwitch = 1;
                break;
            default:
                Serial.println("Unhandled statement");
        }
    } else if (command == 'U') {
        switch(target) {
            case '1':
                bitClear(curSwitchState, SWITCH_SSB_ON);
                break;
            case '2':
                bitClear(curSwitchState, SWITCH_TX_PA);
                break;
            case '3':
                bitClear(curSwitchState, SWITCH_SET_PWR);
                break;
            case '4':
                bitClear(curSwitchState, SWITCH_RX_LNA);
                break;
            case '5':
                bitClear(curSwitchState, SWITCH_SHOW_SWR);
                break;
            case '6': 
                daSwitch = 0;
                break;
            default:
                Serial.println("Unhandled statement");
        }
    }
}