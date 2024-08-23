library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;

entity b2a_cmd_fsm is
  port (
    clk : in std_logic;
    clk_slow : in std_logic;
    rst : in std_logic;

    -- uart
    tx_data : out std_logic_vector(7 downto 0);
    tx_valid : out std_ulogic;
    tx_rdy : in std_logic;

    -- command signals
    command : in std_logic_vector(7 downto 0);
    length : in std_logic_vector(7 downto 0);
    payload : in std_logic_vector(7 downto 0);
    new_cmd : in std_logic;
    new_payload : in std_logic;
    done : out std_logic;

    -- dut signals
    dut_done : in std_logic;
    dut_start : out std_logic;
    x0    : out std_logic_vector(n_bit - 1 downto 0);
    x1    : out std_logic_vector(n_bit - 1 downto 0);
    r0    : out std_logic_vector(n_bit - 1 downto 0);
    c_r0  : out std_logic_vector(n_bit - 1 downto 0);
    c_r1  : out std_logic_vector(n_bit - 1 downto 0);
    c_r2  : out std_logic_vector(n_bit - 2 downto 0);
    c_r3  : out std_logic_vector(n_bit - 2 downto 0);
    c_r4  : out std_logic_vector(n_bit - 2 downto 0);
    a_r0  : out std_logic_vector(n_bit - 2 downto 0);
    a_r1  : out std_logic_vector(n_bit - 2 downto 0);
    a_r2  : out std_logic_vector(n_bit - 2 downto 0);
    x_r   : out std_logic_vector(n_bit - 1 downto 0);
    A0    : in std_logic_vector(n_bit - 1 downto 0);
    A1    : in std_logic_vector(n_bit - 1 downto 0)
  );
end entity;

architecture behavioral of b2a_cmd_fsm is

  -- fsm signals
  type states is (RESET, IDLE, WR_SHARE0, WAIT_SHARE0, WR_SHARE1, WAIT_SHARE1, WR_RAND, WAIT_RAND, INC_RAND, PROC_DONE, SEND_ACK, WAIT_SEND_ACK, WAIT_TX, WAIT_DUT, START_DUT, SEND_RESULT1, WAIT_SEND_RESULT1, SEND_RESULT2, WAIT_SEND_RESULT2);
  signal c_state : states;
  signal n_state : states;

  signal rst_int : std_logic;

  -- dut signals
  signal x0_en : std_logic;
  signal x1_en : std_logic;
  signal r0_en : std_logic;
  signal c_r0_en : std_logic;
  signal c_r1_en : std_logic;
  signal c_r2_en : std_logic;
  signal c_r3_en : std_logic;
  signal c_r4_en : std_logic;
  signal a_r0_en : std_logic;
  signal a_r1_en : std_logic;
  signal a_r2_en : std_logic;
  signal x_r_en : std_logic;

  signal cnt : unsigned(9 downto 0);
  signal cnt_en : std_logic;
  signal cnt_rst : std_logic;

  signal data_cnt : natural range 0 to 10;
  signal rst_data_cnt : std_logic;

  signal dut_start_int : std_logic;
  signal lock : std_logic;

begin

  dut_start <= dut_start_int;

  lock_reg : process(clk_slow)
  begin
    if clk_slow'event and clk_slow = '1' then
      if rst = '1' or dut_done = '1' then
        lock <= '0';
      elsif dut_start_int = '1' then
        lock <= '1';
      else
        lock <= lock;
      end if;
    end if;
  end process;

  start_reg : process(clk_slow)
  begin
    if clk_slow'event and clk_slow = '1' then
      if rst = '1' or dut_done = '1' then
        dut_start_int <= '0';
      elsif c_state = START_DUT and lock = '0' then
        dut_start_int <= '1';
      else
        dut_start_int <= '0';
      end if;
    end if;
  end process;

  data_counter : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' or new_cmd = '1' or rst_data_cnt = '1' then
        data_cnt <= 0;
      elsif new_payload = '1' then
        data_cnt <= data_cnt + 1;
      end if;
    end if;
  end process;

  rand_enable : process(c_state, cnt)
  begin
    if c_state = WR_RAND then
      r0_en   <= cnt(0);
      c_r0_en <= cnt(1);
      c_r1_en <= cnt(2);
      c_r2_en <= cnt(3);
      c_r3_en <= cnt(4);
      c_r4_en <= cnt(5);
      a_r0_en <= cnt(6);
      a_r1_en <= cnt(7);
      a_r2_en <= cnt(8);
      x_r_en  <= cnt(9);
    else
      r0_en   <= '0';
      c_r0_en <= '0';
      c_r1_en <= '0';
      c_r2_en <= '0';
      c_r3_en <= '0';
      c_r4_en <= '0';
      a_r0_en <= '0';
      a_r1_en <= '0';
      a_r2_en <= '0';
      x_r_en  <= '0';
    end if;
  end process;

  counter : process(clk)
  begin
    if clk'event and clk = '1' then
      if cnt_rst = '1' then
        cnt <= (others => '0');
      elsif cnt_en = '1' then
        if to_integer(cnt) = 0 then
          cnt(0) <= '1';
        else
          cnt <= shift_left(cnt, 1);
        end if;
      end if;
    end if;
  end process;

  reg : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        x0 <= (others => '0');
        x1 <= (others => '0');
        r0 <= (others => '0');
        c_r0 <= (others => '0');
        c_r1 <= (others => '0');
        c_r2 <= (others => '0');
        c_r3 <= (others => '0');
        c_r4 <= (others => '0');
        a_r0 <= (others => '0');
        a_r1 <= (others => '0');
        a_r2 <= (others => '0');
        x_r <= (others => '0');
      else
        if x0_en = '1' then
          x0 <= payload;
        end if;
        if x1_en = '1' then
          x1 <= payload;
        end if;
        if r0_en = '1' then
          r0 <= payload;
        end if;
        if c_r0_en = '1' then
          c_r0 <= payload;
        end if;
        if c_r1_en = '1' then
          c_r1 <= payload;
        end if;
        if c_r2_en = '1' then
          c_r2 <= payload(n_bit - 2 downto 0);
        end if;
        if c_r3_en = '1' then
          c_r3 <= payload(n_bit - 2 downto 0);
        end if;
        if c_r4_en = '1' then
          c_r4 <= payload(n_bit - 2 downto 0);
        end if;
        if a_r0_en = '1' then
          a_r0 <= payload(n_bit - 2 downto 0);
        end if;
        if a_r1_en = '1' then
          a_r1 <= payload(n_bit - 2 downto 0);
        end if;
        if a_r2_en = '1' then
          a_r2 <= payload(n_bit - 2 downto 0);
        end if;
        if x_r_en = '1' then
          x_r <= payload;
        end if;
      end if;
    end if;
  end process;

  n_logic : process(c_state, rst, new_cmd, command, new_payload, length, data_cnt, dut_done, tx_rdy, cnt, lock)
  begin
    case(c_state) is
      when RESET =>
        if rst = '1' then
          n_state <= RESET;
        else
          n_state <= IDLE;
        end if;

      when IDLE =>
        if new_cmd = '1' then
          if command = x"01" then
            n_state <= WAIT_SHARE0;
          elsif command = x"02" then
            n_state <= WAIT_RAND;
          elsif command = x"03" then
            n_state <= START_DUT;
          else
            n_state <= RESET;
          end if;
        elsif data_cnt >= to_integer(unsigned(length)) and data_cnt > 0 then
          n_state <= WAIT_SEND_ACK;
        else
          n_state <= IDLE;
        end if;

      when WAIT_SHARE0 =>
        if new_payload = '1' then
          n_state <= WR_SHARE0;
        else
          n_state <= WAIT_SHARE0;
        end if;

      when WR_SHARE0 =>
        n_state <= WAIT_SHARE1;

      when WAIT_SHARE1 =>
        if new_payload = '1' then
          n_state <= WR_SHARE1;
        else
          n_state <= WAIT_SHARE1;
        end if;

      when WR_SHARE1 =>
        n_state <= IDLE;

      when WR_RAND =>
        if cnt(9) = '1' then
          n_state <= IDLE;
        else
          n_state <= WAIT_RAND;
        end if;

      when WAIT_RAND =>
        if new_payload = '1' then
          n_state <= INC_RAND;
        else
          n_state <= WAIT_RAND;
        end if;

      when INC_RAND =>
        n_state <= WR_RAND;

      when PROC_DONE =>
        n_state <= IDLE;

      when WAIT_SEND_ACK =>
        if tx_rdy = '1' then
          n_state <= SEND_ACK;
        else
          n_state <= WAIT_SEND_ACK;
        end if;

      when SEND_ACK =>
        n_state <= WAIT_TX;

      when WAIT_TX =>
        if tx_rdy = '1' then
          n_state <= PROC_DONE;
        else
          n_state <= WAIT_TX;
        end if;

      when START_DUT =>
        if lock = '1' then
          n_state <= WAIT_DUT;
        else
          n_state <= START_DUT;
        end if;

      when WAIT_DUT =>
        if dut_done = '1' then
          n_state <= SEND_RESULT1;
        else
          n_state <= WAIT_DUT;
        end if;

      when SEND_RESULT1 =>
        n_state <= WAIT_SEND_RESULT1;

      when WAIT_SEND_RESULT1 =>
        if tx_rdy = '1' then
          n_state <= SEND_RESULT2;
        else
          n_state <= WAIT_SEND_RESULT1;
        end if;

      when SEND_RESULT2 =>
        n_state <= WAIT_SEND_RESULT2;

      when WAIT_SEND_RESULT2 =>
        if tx_rdy = '1' then
          n_state <= PROC_DONE;
        else
          n_state <= WAIT_SEND_RESULT2;
        end if;

      when others =>
        n_state <= RESET;
    end case;
  end process;


  o_logic : process(c_state)
  begin
    x0_en <= '0';
    x1_en <= '0';
    rst_int <= '0';
    cnt_rst <= '0';
    cnt_en <= '0';
    done <= '0';
    rst_data_cnt <= '0';
    tx_valid <= '0';
    tx_data <= (others => '0');
    case(c_state) is
      when WR_SHARE0 =>
        x0_en <= '1';
      when WR_SHARE1 =>
        x1_en <= '1';
      when INC_RAND =>
        cnt_en <= '1';
      when RESET =>
        rst_int <= '1';
        cnt_rst <= '1';
      when SEND_ACK =>
        tx_valid <= '1';
        tx_data <= x"01";
        cnt_rst <= '1';
      when WAIT_TX =>
        tx_data <= x"01";
      when PROC_DONE =>
        done <= '1';
        rst_data_cnt <= '1';
      when SEND_RESULT1 =>
        tx_valid <= '1';
        tx_data <= A0;
      when SEND_RESULT2 =>
        tx_valid <= '1';
        tx_data <= A1;
      when WAIT_SEND_RESULT1 =>
        tx_data <= A0;
      when WAIT_SEND_RESULT2 =>
        tx_data <= A1;
      when others =>
        x0_en <= '0';
        x1_en <= '0';
        rst_int <= '0';
        cnt_rst <= '0';
        cnt_en <= '0';
        done <= '0';
        tx_valid <= '0';
        tx_data <= (others => '0');
    end case;
  end process;

  state_mem : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        c_state <= RESET;
      else
        c_state <= n_state;
      end if;
    end if;
  end process;


end architecture;
